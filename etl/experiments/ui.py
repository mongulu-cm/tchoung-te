import os
from typing import Any

import chainlit as cl
import pandas as pd
import sentry_sdk
from langchain_community.document_loaders import CSVLoader
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_community.vectorstores import FAISS
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from sqlalchemy import  create_engine
from langchain.tools.retriever import create_retriever_tool

sentry_sdk.init(
    dsn="https://a38e91a66c70912c38406fef32d86809@o4504301629407232.ingest.sentry.io/4506436450844672",
    # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions.We recommend adjusting this value in production.
    profiles_sample_rate=1.0,
)

CSV_FILE_PATH = "ref-rna-real-mars-2022-enriched-qualified.csv"

def create_our_sql_agent():
    df = pd.read_csv(CSV_FILE_PATH)
    df = df.rename(
            columns={
                "id": "id_association",
                "objet": "description",
                "adrs": "adresse_complete",
                "dept": "departement",
                "region": "region",
                "social_object1_libelle": "objectif_principal_association",
                "titre": "nom_association",
                "facebook_url": "url_page_facebook",
                "helloasso_url": "url_page_helloasso",
                "adrs_numvoie": "numero_voie_adresse",
                "adrs_typevoie": "type_voie_adresse",
                "adrs_libvoie": "nom_rue_adresse",
                "adrs_codepostal": "code_postal",
                "adrs_libcommune": "ville",
                "siteweb": "url_site_web",
                "social_object2_libelle": "objectif_secondaire_association",
                "longitude": "longitude",
                "latitude": "latitude",
            }
        )

    # Create a SQLite database and load the DataFrame into a table
    engine = create_engine("sqlite:///ref-rna-real-mars-2022-enriched-qualified.db")
    df.to_sql("associations", engine, if_exists="replace", index=False)
    # Initialize a SQLDatabase wrapper for LangChain
    db = SQLDatabase(engine=engine)

    examples = [
            {
                "input": "Donne mois les associations situés à Lyon",
                "query": "SELECT * FROM associtions WHERE ville like '%Lyon%'",
            },
            {
                "input": "Combien d'associations se trouvent en bretagne",
                "query": "SELECT COUNT(id_association) FROM associtions WHERE region like '%Bretagne%'",
            },
            {
                "input": "Combien d'associations à marseille ont une page facebook",
                "query": "SELECT COUNT(id_association) FROM associtions WHERE ville like '%Marseille%' AND url_page_facebook NOT NULL",
            },
        ]

    example_selector = SemanticSimilarityExampleSelector.from_examples(
            examples, OpenAIEmbeddings(), FAISS, k=5, input_keys=["input"]
        )

    system_prefix = """
            Tu es un agent conçu pour interagir avec une base de données SQL.

            La base de données SQL contient la table associations qui répertorie les associations camerounaises en France.

            La table contient des détails sur l'association tels que sa description, son objectif, son adresse, ses coordonnées GPS.

            Utilise l'historique de messages suivants {chat_history} comme contexte de discussion.

            À partir d'une question d'entrée, créez une requête syntaxiquement correcte en {dialect} à exécuter, puis examinez les résultats de la requête et retournez la réponse.
            Sauf si l'utilisateur spécifie un nombre spécifique d'exemples qu'il souhaite obtenir, limitez votre requête à au plus {top_k} résultats.
            Vous pouvez ordonner les résultats par une colonne pertinente pour retourner les exemples les plus intéressants dans la base de données.
            Ne demandez jamais toutes les colonnes d'une table spécifique, demandez uniquement les colonnes pertinentes données par la question.
            Vous avez accès à des outils pour interagir avec la base de données.
            Utilisez uniquement les outils donnés. Utilisez uniquement les informations retournées par les outils pour construire votre réponse finale.
            Vous DEVEZ vérifier votre requête avant de l'exécuter. Si vous obtenez une erreur lors de l'exécution d'une requête, réécrivez la requête et essayez à nouveau.

            Corrigez toujours les noms de villes, régions et département pour correspondre à ceux situés en France lors de l'écriture des requêtes.

            Corrigez toujours la casse de l'utilisateur pour correspondre aux données dans la base de données lors de l'écriture de vos requêtes.
            NE FAITES PAS de déclarations DML (INSERT, UPDATE, DELETE, DROP, etc.) dans la base de données.

            NE FAIT PAS APPARAITRE DE SQL DANS LA REPONSE FINALE.

            Fournissez toujours une réponse claire et structurée en utilisant le nom (mis en gras) de l'association accompagné d'un résumé de sa description,
            ajoute l'adresse complete telle que écrit dans la colonne adresse_complete et utiliser les latitude et longitude pour générer un lien google maps.
            Si possible insérer les URL des associations basés sur les url facebook ou helloasso stockés en base.
            Lorsque cela est pertinent, utilisez des points et des listes pour structurer vos réponses.
            Si possible insérer les URL des associations vers les différentes pages.

            Si la question ne semble pas liée à la base de données où à la discussion, retournez simplement "Je ne sais pas, veuillez consulter la page https://tchoung-te.mongulu.cm pour plus d'infos" comme réponse.
            Voici quelques exemples de questions d'utilisateurs et leurs requêtes SQL correspondantes :
        """
    few_shot_prompt = FewShotPromptTemplate(
            example_selector=example_selector,
            example_prompt=PromptTemplate.from_template(
                "User input: {input}\nSQL query: {query}"
            ),
            input_variables=["input", "dialect", "top_k","chat_history"],
            prefix=system_prefix,
            suffix="",
        )

    full_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate(prompt=few_shot_prompt),
                HumanMessagePromptTemplate.from_template("{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )

    sql_agent = create_sql_agent(
            llm=ChatOpenAI(
            temperature=0,
            model_name="gpt-4o-mini-2024-07-18",
        ),
            db=db, prompt=full_prompt, verbose=True, agent_type="openai-tools"
        )

    return sql_agent


def create_retriever():
    embedding_pth = "embeddings"
    embeddings = OpenAIEmbeddings()
    if os.path.exists(embedding_pth):
        vectors = FAISS.load_local(embedding_pth, embeddings,allow_dangerous_deserialization=True)
    else:
        loader = CSVLoader(
            file_path=CSV_FILE_PATH, encoding="utf-8"
        )
        data = loader.load()
        vectors = FAISS.from_documents(data, embeddings)
        vectors.save_local(embedding_pth)

    retriever = vectors.as_retriever()
    return retriever

@cl.on_chat_start
async def main():
    """
    Main function to be called when a chat starts
    """
    # --- Création de l'agent SQL ---
    sql_agent = create_our_sql_agent()
    from langchain.agents import tool
    @tool
    def sql_tool_func(query: str) -> str:
        """utile pour répondre aux questions non numériques (dont le résulat est un texte) comme sur une association en particulier"""
        return sql_agent.invoke({"input": query,
                "top_k": 5,
                "dialect": "SQLite",
                "chat_history": cl.user_session.get("history"),
                "agent_scratchpad": [],})

    # --- Définition de la fonction pour l'outil Retriever ---
    retriever = create_retriever()
    retriever_tool = create_retriever_tool(
        retriever,
        "retriever_tool",
        "utile pour répondre aux questions non numériques (dont le résulat est un texte) comme sur une association en particulier",
    )

    # --- Initialisation de l'agent avec les deux outils ---
    llm = ChatOpenAI(temperature=0,model="gpt-4o-mini-2024-07-18")
    tools = [sql_tool_func,retriever_tool]
    llm_with_tools = llm.bind_tools(tools)

    from langchain_core.prompts import MessagesPlaceholder


    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """Vous êtes un assistant IA qui fournit des informations sur les associations camerounaises en France. Vous recevez une question et fournissez une réponse claire et structurée. Lorsque cela est pertinent, utilisez des points et des listes pour structurer vos réponses.
                Utilisez les outils à votre disposition pour répondre aux questions des utilisateurs. Si vous ne connaissez pas la réponse après résultat des outils,dites simplement que vous ne savez pas, n'essayez pas d'inventer une réponse.
                Si la question posée est dans une langue parlée en Afrique ou au Cameroun ou demande une traduction dans une de ces langues, répondez que vous ne savez pas et demandez à l'utilisateur de reformuler sa question.
                Si vous connaissez la réponse à la question mais que cette réponse ne provient pas des résulats des outils ou n'est pas relatif aux associations, répondez que vous ne savez pas et demandez à l'utilisateur de reformuler sa question.
                """,
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    from langchain.agents.format_scratchpad.openai_tools import (
        format_to_openai_tool_messages,
    )
    from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
    from langchain.agents import AgentExecutor

    agent = (
        {
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: format_to_openai_tool_messages(
                x["intermediate_steps"]
            ),
            "chat_history": lambda x: x["chat_history"],
        }
        | prompt
        | llm_with_tools
        | OpenAIToolsAgentOutputParser()
    )
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    cl.user_session.set("agent", agent_executor)
    cl.user_session.set("history", [])


@cl.on_message
async def main_message(message: cl.Message):
    """
    Main function to be called when a message is received

    Args:
        message (cl.Message): User message on chainlit UI
    """
    history = cl.user_session.get("history")
    llm_agent = cl.user_session.get("agent")

    msg = cl.Message(content="")
    await msg.send()

    def fetching_answer(question):
        return llm_agent.invoke(
            {
                "input": question,
                "top_k": 5,
                "dialect": "SQLite",
                "chat_history": history,
                "agent_scratchpad": [],
            },
            return_only_outputs=True,
        )["output"]

    response = await cl.make_async(fetching_answer)(message.content)

    history_entry = f"""
    Question: {message.content}\n
    Réponse: {response}
    """
    history.append(history_entry)

    cl.user_session.set("history", history)

    # Send the response
    msg.content = response

    await msg.update()

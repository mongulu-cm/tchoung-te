import os
from typing import Any

import chainlit as cl
import pandas as pd
import sentry_sdk
from langchain.chains import ConversationalRetrievalChain
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.document_loaders.csv_loader import CSVLoader
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
from sqlalchemy import Engine, create_engine

# sentry_sdk.init(
#     dsn="https://a38e91a66c70912c38406fef32d86809@o4504301629407232.ingest.sentry.io/4506436450844672",
#     # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring.
#     traces_sample_rate=1.0,
#     # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions.We recommend adjusting this value in production.
#     profiles_sample_rate=1.0,
# )

# system_template = """Vous êtes un assistant IA qui fournit des informations sur
# les associations camerounaises en France. Vous recevez une question et
# fournissez une réponse claire et structurée. Lorsque cela est pertinent,
# utilisez des points et des listes pour structurer vos réponses.

# Utilisez les éléments de contexte suivants pour répondre à la question de
# l'utilisateur. Si vous ne connaissez pas la réponse, dites simplement que vous
# ne savez pas, n'essayez pas d'inventer une réponse.

# Si vous souhaitez connaître le nombre d'associations, je vous recommande de
# visiter le site web "tchoung-te.mongulu.cm" pour obtenir des informations
# actualisées à ce sujet.
# ----------------
# {context}"""


CSV_FILE_PATH = "ref-rna-real-mars-2022-enriched-qualified.csv"


def update_sqlite_database() -> Engine:
    """Updates the SQLite database with data from a CSV file.

    Reads the CSV file at the provided path, renames the columns,
    and inserts the contents into a SQLite table called 'associations'.
    If the table already exists, it is replaced.

    Returns the SQLAlchemy Engine for the SQLite database.
    """
    df = pd.read_csv(CSV_FILE_PATH)

    # Rename columns
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

    engine = create_engine("sqlite:///Associations-cameronaises-de-France.sqlite")

    df.to_sql("associations", engine, index=False, if_exists="replace")

    return engine


def build_llm_agent(engine: Engine) -> Any:
    """
    Builds an SQL agent to interact with the associations database.

    The agent is designed to take a natural language user input, convert it to
    an SQL query to run against the associations database, execute the query,
    and return a response summarizing the results.

    It uses the OpenAI ChatGPT model fine-tuned with a few-shot learning prompt
    to map user inputs to SQL queries. The prompt provides examples of user
    questions and corresponding SQL queries.

    The agent limits results to top_k to avoid large result sets. It also
    sanitizes user input and constructs the response using conventions outlined
    in the prompt.
    """
    db = SQLDatabase(engine=engine)

    # TODO: add more examples for a better database indexing
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
        input_variables=["input", "dialect", "top_k", "chat_history"],
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

    llm = ChatOpenAI(
        # max_tokens=500,
        temperature=0,
        # model_name="gpt-4",
        model_name="gpt-3.5-turbo",
    )

    agent = create_sql_agent(
        llm=llm, db=db, prompt=full_prompt, verbose=True, agent_type="openai-tools"
    )

    return agent


@cl.on_chat_start
async def main():
    """
    Main function to be called when a chat starts
    """

    sqlite_engine = update_sqlite_database()
    llm_agent = build_llm_agent(engine=sqlite_engine)

    cl.user_session.set("agent", llm_agent)
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
import os
import pandas as pd
from sqlalchemy import create_engine
from langchain.llms import OpenAI
from langchain.agents import initialize_agent, Tool
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain.document_loaders import CSVLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_community.agent_toolkits import create_sql_agent

# Set your OpenAI API key (replace with your key)
# --- Préparation de la base SQL à partir du CSV ---
# Read the CSV file into a pandas DataFrame
df = pd.read_csv("../ref-rna-real-mars-2022-enriched-qualified.csv")
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

# --- Définition de la fonction pour l'outil SQL ---
def sql_tool_func(query: str) -> str:
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
        input_variables=["input", "dialect", "top_k"],
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
    return agent.invoke({"input": query})

# --- Définition de la fonction pour l'outil Retriever ---
def retriever_tool_func(query: str) -> str:
    # Load the CSV documents using LangChain's CSVLoader
    loader = CSVLoader(file_path="../ref-rna-real-mars-2022-enriched-qualified.csv")
    docs = loader.load()
    # Create embeddings using OpenAIEmbeddings and build a FAISS vectorstore
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(docs, embeddings)
    # Create a retriever that will return the top 3 matching documents
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    # Build a simple RetrievalQA chain using the retriever
    qa_chain = RetrievalQA.from_chain_type(llm=OpenAI(temperature=0), chain_type="stuff", retriever=retriever)
    return qa_chain.run(query)

# --- Création des objets Tool ---
sql_tool = Tool(
    name="Retriever Tool 1",
    func=sql_tool_func,
    description="Useful for answering numerical questions'"
)
retriever_tool = Tool(
    name="Retriever Tool 2",
    func=retriever_tool_func,
    description="Useful for non numerical questions'"
)

# --- Initialisation de l'agent avec les deux outils ---
llm = ChatOpenAI(temperature=0,model="gpt-4o-mini-2024-07-18")
tools = [sql_tool, retriever_tool]
agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)

# --- Exemples d'utilisation ---
# Question structurée pour le SQL
query_sql = "Combien d'associations y a t-il à Grenoble ?"
print("Réponse SQL:", agent.run(query_sql))

# Question libre pour le Retriever
query_retriever = "C'est quoi l'aci ?"
print("Réponse Retriever:", agent.run(query_retriever))

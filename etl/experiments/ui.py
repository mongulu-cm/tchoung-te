import os
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
import chainlit as cl

system_template = """Vous êtes un assistant AI  qui fournit des informations sur les associations camerounaises en France.
Vous recevez une question et fournissez une réponse claire et structurée.Lorsque cela est pertinent, utilisez des points et des listes pour structurer vos réponses.

Utilisez les éléments de contexte suivants pour répondre à la question de l'utilisateur.
Si vous ne connaissez pas la réponse, dites simplement que vous ne savez pas, n'essayez pas d'inventer une réponse.
----------------
{context}"""
messages = [
    SystemMessagePromptTemplate.from_template(system_template),
    HumanMessagePromptTemplate.from_template("{question}"),
]
CHAT_PROMPT = ChatPromptTemplate.from_messages(messages)


loader = CSVLoader(file_path="ref-rna-real-mars-2022-enriched-qualified.csv", encoding="utf-8")
data = loader.load()
embeddings = OpenAIEmbeddings()
vectors = FAISS.from_documents(data, embeddings)

llm = ChatOpenAI(max_tokens=500,temperature=0,model_name="gpt-3.5-turbo")
chain_type_kwargs = {"prompt": CHAT_PROMPT}
qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectors.as_retriever(search_kwargs={"k": 3}),
    chain_type_kwargs=chain_type_kwargs,
    return_source_documents=True
)

@cl.langchain_factory(use_async=True)
def factory():
    return qa

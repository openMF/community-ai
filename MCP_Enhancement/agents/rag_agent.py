import os
import logging
from typing import List

# LangChain Imports
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

# Config Import
from MCP_Enhancement.config import get_settings

# Configure Logging
logger = logging.getLogger(__name__)

# --- Constants ---
PROMPT_TEMPLATE = """
You are an expert technical assistant for the Mifos Community.
Answer the user's question based ONLY on the following context. 
If the answer is not in the context, say "I don't have enough information in my knowledge base to answer that."

--- Context ---
{context}
--- End Context ---

User Question: {question}
"""


def get_vectorstore():
    """
    Initializes the connection to the local Chroma vector database.
    """
    settings = get_settings()
    embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY.get_secret_value())

    # Check if DB exists
    if not os.path.exists(settings.VECTOR_DB_PATH):
        logger.warning(f"Vector DB not found at {settings.VECTOR_DB_PATH}. Please run the ingestion script first.")
        return None

    return Chroma(
        persist_directory=settings.VECTOR_DB_PATH,
        embedding_function=embeddings
    )


def query_docs(question: str) -> str:
    """
    Retrieves relevant documentation and synthesizes an answer.
    """
    try:
        # 1. Get the Vector DB
        db = get_vectorstore()
        if not db:
            return "Error: The knowledge base has not been built yet. Please ask an admin to run the ingestion script."

        # 2. Search for relevant chunks (Top 3)
        # We assume the DB contains the 'Static' Manuals/Guides
        results = db.similarity_search_with_score(question, k=3)

        if not results:
            return "I couldn't find any relevant documentation for your query."

        # 3. Format context
        context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])

        # 4. Generate Answer using LLM
        settings = get_settings()
        llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0,
            api_key=settings.OPENAI_API_KEY.get_secret_value()
        )

        prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        chain = prompt | llm

        response = chain.invoke({"context": context_text, "question": question})
        return response.content

    except Exception as e:
        logger.error(f"RAG Query failed: {e}")
        return f"Error retrieving documentation: {str(e)}"
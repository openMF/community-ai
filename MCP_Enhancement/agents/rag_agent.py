import os
import logging
import time
from typing import List

# Pinecone & LangChain Imports
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

# Config Import
# Ensure your config.py is set up to read PINECONE_API_KEY and PINECONE_INDEX_NAME
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
    Initializes the connection to the Pinecone vector database.
    """
    settings = get_settings()

    # 1. Initialize Embeddings (same as before)
    embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY.get_secret_value())

    # 2. Initialize Pinecone Client
    pc = Pinecone(api_key=settings.PINECONE_API_KEY.get_secret_value())

    # 3. Check/Create Index
    index_name = settings.PINECONE_INDEX_NAME
    existing_indexes = [index.name for index in pc.list_indexes()]

    if index_name not in existing_indexes:
        # Create the index if it doesn't exist (Phase 4 Setup)
        logger.info(f"Creating new Pinecone index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=1536,  # Matches OpenAI text-embedding-3-small
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        # Wait a moment for index to initialize
        while not pc.describe_index(index_name).status['ready']:
            time.sleep(1)

    # 4. Connect to the Index via LangChain wrapper
    vectorstore = PineconeVectorStore(
        index_name=index_name,
        embedding=embeddings
    )

    return vectorstore


def query_docs(question: str) -> str:
    """
    Retrieves relevant documentation from Pinecone and synthesizes an answer.
    """
    try:
        # 1. Get the Vector Store (Pinecone)
        vectorstore = get_vectorstore()

        # 2. Search for relevant chunks (Top 3)
        # using similarity_search functionality provided by LangChain's Pinecone wrapper
        results = vectorstore.similarity_search(question, k=3)

        if not results:
            return "I couldn't find any relevant documentation for your query."

        # 3. Format context
        context_text = "\n\n---\n\n".join([doc.page_content for doc in results])

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
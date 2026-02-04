import os
import logging
import time
from typing import List

# Pinecone & LangChain Imports
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate

# Robust Config Import
# We try multiple paths to ensure this works regardless of how you run it
try:
    from MCP_Enhancement.config import get_settings
except ImportError:
    try:
        from config import get_settings
    except ImportError:
        # Fallback if running from inside the folder
        from ..config import get_settings

# Configure Logging
logger = logging.getLogger(__name__)

# --- THE EXPERT PROMPT (Guarantees the "Better Answer") ---
MIFOS_PROMPT_TEMPLATE = """
You are the **Mifos Technical Assistant** — helpful, professional, and friendly.

### Core Architectural Facts (ALWAYS USE THESE):
- **Apache Fineract** is the open-source **core banking engine** (The Backend).
- **Mifos X** is the **solution and distribution** built on top of Fineract (The Frontend/Solution).

### Response Guidelines
1. Combine the "Core Architectural Facts" above with the retrieved context below.
2. If the answer is not in the context, relying on the core facts is permitted for basic definitions.
3. Answer the user's question clearly and professionally.

### Retrieved Context
{context}

### User Question
{question}

### Helpful Answer:
"""

def get_vectorstore():
    """
    Initializes the connection to the Pinecone vector database.
    Creates the index automatically if it does not exist.
    """
    settings = get_settings()

    # 1. Initialize Embeddings
    embeddings = OpenAIEmbeddings(
        api_key=settings.OPENAI_API_KEY.get_secret_value(),
        model="text-embedding-3-small"
    )

    # 2. Initialize Pinecone Client
    pc = Pinecone(api_key=settings.PINECONE_API_KEY.get_secret_value())

    # 3. Check/Create Index
    index_name = settings.PINECONE_INDEX_NAME
    existing_indexes = [index.name for index in pc.list_indexes()]

    if index_name not in existing_indexes:
        logger.info(f"🧠 Creating new Pinecone index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=1536,  # Matches text-embedding-3-small
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        # Wait for initialization
        while not pc.describe_index(index_name).status['ready']:
            time.sleep(1)
        logger.info("✅ Index created successfully!")

    # 4. Connect via LangChain
    return PineconeVectorStore(
        index_name=index_name,
        embedding=embeddings
    )

def query_docs(question: str) -> str:
    """
    Retrieves relevant documentation and synthesizes an answer using the Expert Prompt.
    """
    try:
        # 1. Get the Vector Store
        vectorstore = get_vectorstore()

        # 2. Setup LLM
        settings = get_settings()
        llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0,
            api_key=settings.OPENAI_API_KEY.get_secret_value()
        )

        # 3. Build the Expert Chain
        QA_CHAIN_PROMPT = PromptTemplate(
            input_variables=["context", "question"],
            template=MIFOS_PROMPT_TEMPLATE,
        )

        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
            chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
        )

        # 4. Execute
        result = qa_chain.invoke({"query": question})
        return result['result']

    except Exception as e:
        logger.error(f"RAG Query failed: {e}")
        return f"Error retrieving documentation: {str(e)}"
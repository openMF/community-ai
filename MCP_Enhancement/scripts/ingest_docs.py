import os
import logging
import sys

# --- FORCE INJECTION START ---
# We manually load the settings and push the key into the system environment
# so the LangChain library can't miss it.
try:
    # Adjust path to find config
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from MCP_Enhancement.config import get_settings
    settings = get_settings()
    # This line forces the key into the OS environment at runtime
    os.environ["PINECONE_API_KEY"] = settings.PINECONE_API_KEY.get_secret_value()
except Exception as e:
    print(f"Pre-flight config check failed: {e}")
# --- FORCE INJECTION END ---

# Now proceed with the rest of the imports
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone, ServerlessSpec

# Fix path to ensure we can import config.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from MCP_Enhancement.config import get_settings
except ImportError:
    from MCP_Enhancement.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingest")

# Paths relative to the script location
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(BASE_DIR, "docs")


def main():
    settings = get_settings()

    # 1. Check if docs directory exists
    if not os.path.exists(DATA_PATH):
        logger.error(f"Directory NOT found at: {DATA_PATH}")
        return

    # 2. Load Documents (PDFs and Markdown)
    logger.info(f"Loading documents from: {DATA_PATH}...")

    pdf_loader = DirectoryLoader(DATA_PATH, glob="**/*.pdf", loader_cls=PyPDFLoader)
    md_loader = DirectoryLoader(DATA_PATH, glob="**/*.md", loader_cls=TextLoader)

    docs = []
    docs.extend(pdf_loader.load())
    docs.extend(md_loader.load())

    if not docs:
        logger.warning(f"No documents found in {DATA_PATH}.")
        return

    logger.info(f"Loaded {len(docs)} documents.")

    # 3. Split Text into Chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        add_start_index=True
    )
    chunks = text_splitter.split_documents(docs)
    logger.info(f"Split into {len(chunks)} text chunks.")

    # 4. Pinecone Initialization (Phase 4 Logic)
    # Extract the raw string from SecretStr for the Pinecone client
    pc_api_key = settings.PINECONE_API_KEY.get_secret_value()
    pc = Pinecone(api_key=pc_api_key)
    index_name = settings.PINECONE_INDEX_NAME

    # Ensure index exists
    if index_name not in [index.name for index in pc.list_indexes()]:
        logger.info(f"Creating index {index_name}...")
        pc.create_index(
            name=index_name,
            dimension=1536, # Standard for OpenAI text-embedding-3-small or ada-002
            metric='cosine',
            spec=ServerlessSpec(cloud='aws', region='us-east-1')
        )

    # 5. Upload to Pinecone
    logger.info(f"Uploading {len(chunks)} chunks to Pinecone index: {index_name}...")

    try:
        # Extract OpenAI key
        openai_key = settings.OPENAI_API_KEY.get_secret_value()
        embeddings = OpenAIEmbeddings(api_key=openai_key)

        # UPDATED: Explicitly pass pinecone_api_key to the VectorStore
        PineconeVectorStore.from_documents(
            documents=chunks,
            embedding=embeddings,
            index_name=index_name,
            pinecone_api_key=pc_api_key  # Pass key here explicitly
        )
        logger.info("✅ Ingestion Complete! Your Mifos Knowledge Base is now in the cloud.")
    except Exception as e:
        logger.error(f"Failed to upload to Pinecone: {e}")


if __name__ == "__main__":
    main()
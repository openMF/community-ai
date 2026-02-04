import os
import logging
import shutil
import sys

# LangChain Imports
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

# --- Path Fix for Contribution Folder ---
# This ensures that 'src' can be found even if running from the root of the repo
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

try:
    from mcp_enhancement.src.core.config import get_settings
except ImportError:
    # Fallback if you are running directly inside the mcp_enhancement/src folder
    from MCP_Enhancement.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingest")

# --- Dynamic Path Logic ---
# This looks for 'docs' inside your specific enhancement folder
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
DATA_PATH = os.path.join(BASE_DIR, "docs")


def main():
    settings = get_settings()

    # 1. Check if docs directory exists
    if not os.path.exists(DATA_PATH):
        logger.error(f"Directory NOT found at: {DATA_PATH}")
        logger.error("Please ensure you created 'mcp_enhancement/docs/' and added files there.")
        return

    # 2. Load Documents (PDFs and Markdown)
    logger.info(f"Loading documents from: {DATA_PATH}...")

    # use_multithreading=True speeds up loading for many files
    pdf_loader = DirectoryLoader(DATA_PATH, glob="**/*.pdf", loader_cls=PyPDFLoader, show_progress=True)
    md_loader = DirectoryLoader(DATA_PATH, glob="**/*.md", loader_cls=TextLoader, show_progress=True)

    docs = []
    try:
        docs.extend(pdf_loader.load())
        docs.extend(md_loader.load())
    except Exception as e:
        logger.error(f"Error loading files: {e}")
        return

    if not docs:
        logger.warning(f"No .pdf or .md documents found in {DATA_PATH}.")
        return

    logger.info(f"Loaded {len(docs)} documents.")

    # 3. Split Text into Chunks
    # We use a slightly smaller overlap for technical docs to keep context tight
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        add_start_index=True
    )
    chunks = text_splitter.split_documents(docs)
    logger.info(f"Split into {len(chunks)} text chunks.")

    # 4. Save to Vector DB (Chroma)
    # The path comes from your config.py (e.g., mcp_enhancement/data/chroma_db)
    if os.path.exists(settings.VECTOR_DB_PATH):
        logger.info(f"Clearing existing database at {settings.VECTOR_DB_PATH}...")
        shutil.rmtree(settings.VECTOR_DB_PATH)

    logger.info(f"Creating embeddings and saving to: {settings.VECTOR_DB_PATH}...")

    try:
        embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY.get_secret_value())

        Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=settings.VECTOR_DB_PATH
        )
        logger.info("✅ Ingestion Complete! Your RAG agent is now trained.")
    except Exception as e:
        logger.error(f"Failed to create embeddings: {e}")
        logger.error("Check if your OPENAI_API_KEY is correct in mcp_enhancement/.env")


if __name__ == "__main__":
    main()
import os
import sys
from pinecone import Pinecone
from dotenv import load_dotenv

# Ensure we can find the config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def verify_setup():
    load_dotenv()
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "mifos-knowledge-base")

    if not api_key:
        print("❌ Error: PINECONE_API_KEY not found in .env file.")
        return

    print(f"📡 Connecting to Pinecone...")
    try:
        pc = Pinecone(api_key=api_key)

        # 1. Check Connection & Indexes
        indexes = pc.list_indexes()
        index_names = [idx.name for idx in indexes]

        print(f"✅ Successfully connected to Pinecone!")
        print(f"📂 Available Indexes: {index_names}")

        if index_name not in index_names:
            print(f"⚠️ Warning: Index '{index_name}' does not exist yet.")
            print("👉 Run 'python MCP_Enhancement/scripts/ingest_docs.py' to create it.")
        else:
            # 2. Check Index Stats
            idx = pc.Index(index_name)
            stats = idx.describe_index_stats()
            vector_count = stats['total_vector_count']

            print(f"✨ Index '{index_name}' is ACTIVE.")
            print(f"📊 Total Vectors (Chunks) stored: {vector_count}")

            if vector_count == 0:
                print("ℹ️ Your index is empty. Time to run the ingestion script!")
            else:
                print("🚀 Phase 4 RAG is ready for queries.")

    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")


if __name__ == "__main__":
    verify_setup()
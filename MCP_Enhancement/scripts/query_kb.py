import os
import logging
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# Robust Config Loading
try:
    from MCP_Enhancement.src.core.config import get_settings
except ImportError:
    from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# --- The Expert Prompt (The Personality you built in Phase 4) ---
MIFOS_PROMPT_TEMPLATE = """
You are the **Mifos Technical Assistant** — helpful, professional, and friendly.

### Core Architectural Facts
- **Apache Fineract** is the open-source **core banking engine**.
- **Mifos X** is a **solution and distribution** built on top of Apache Fineract.

### Response Guidelines
1. Answer **strictly using the retrieved context provided below**.
2. If the answer is **not present**, clearly say you do not have that info in the current Mifos docs.
3. **Do not guess or invent details.** Accuracy is critical for financial software.

### Retrieved Context
{context}

### User Question
{question}

### Helpful Answer:
"""

def query_mifos_ai(question: str) -> str:
    """
    Main callable function for the Orchestrator.
    Accepts a query and returns a grounded, professional answer.
    """
    try:
        # 1. Setup Embeddings and LLM
        openai_key = settings.OPENAI_API_KEY.get_secret_value()
        embeddings = OpenAIEmbeddings(api_key=openai_key)
        llm = ChatOpenAI(model=settings.OPENAI_MODEL, api_key=openai_key, temperature=0)

        # 2. Connect to Pinecone
        vectorstore = PineconeVectorStore(
            index_name=settings.PINECONE_INDEX_NAME,
            embedding=embeddings
        )

        # 3. Build the Prompt
        QA_CHAIN_PROMPT = PromptTemplate(
            input_variables=["context", "question"],
            template=MIFOS_PROMPT_TEMPLATE,
        )

        # 4. Create the RAG Chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
            chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
        )

        # 5. Execute
        result = qa_chain.invoke({"query": question})
        return result['result']

    except Exception as e:
        logger.error(f"Knowledge Base Query Failed: {e}")
        return "I'm sorry, I'm having trouble accessing my documentation archives right now."

# Keep this for quick manual testing from terminal
if __name__ == "__main__":
    import sys
    test_query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is Mifos X?"
    print(query_mifos_ai(test_query))
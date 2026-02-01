import os
import sys
import logging
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from MCP_Enhancement.config import get_settings

    settings = get_settings()
    # Force the key into the environment for LangChain
    os.environ["PINECONE_API_KEY"] = settings.PINECONE_API_KEY.get_secret_value()
except ImportError:
    print("❌ Could not import config. Ensure you are running from the root folder.")
    sys.exit(1)

logging.basicConfig(level=logging.ERROR)

def query_mifos_ai(question: str):
    print(f"\n🤔 Question: {question}")

    # 1. Setup Embeddings and LLM
    openai_key = settings.OPENAI_API_KEY.get_secret_value()
    embeddings = OpenAIEmbeddings(api_key=openai_key)
    llm = ChatOpenAI(model=settings.OPENAI_MODEL, api_key=openai_key, temperature=0)

    # 2. Define the Custom Grounding Prompt
    template = """
    You are the **Mifos Technical Assistant** — helpful, professional, and friendly, with a light touch of wit when appropriate.

    ### Core Architectural Facts (Always True)
    - **Apache Fineract** is the open-source **core banking engine**.
    - **Mifos X** is a **solution and distribution** built on top of Apache Fineract.
    - They are distinct: Mifos X provides user-facing applications, configurations, and workflows, while Apache Fineract handles the core banking logic.

    ### Response Guidelines
    1. If the question is **clearly unrelated to financial services, software, politely explain that Mifos is a financial services platform and you cannot help with that request.
    2. For **financial, technical, or Mifos-related questions**, answer **strictly using the retrieved context provided below**.
    3. If the answer is **not present in the provided context**, clearly say that you do not have that information in the current Mifos documentation.
    4. **Do not guess, infer, or invent details.** Accuracy is more important than completeness.
    5. When possible, provide **clear, step-by-step explanations** suitable for developers and contributors.

    ### Retrieved Context
    {context}

    ### User Question
    {question}

    ### Helpful Answer
    """

    QA_CHAIN_PROMPT = PromptTemplate(
        input_variables=["context", "question"],
        template=template,
    )

    # 3. Connect to the Vector Store
    vectorstore = PineconeVectorStore(
        index_name=settings.PINECONE_INDEX_NAME,
        embedding=embeddings
    )

    # 4. Create the RAG Chain with the Custom Prompt
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True,
        chain_type_kwargs={"prompt": QA_CHAIN_PROMPT} # Injects your custom rules
    )

    # 5. Execute Query
    result = qa_chain.invoke({"query": question})

    print(f"\n🤖 AI Answer:\n{result['result']}")

    print("\n📚 Sources Used:")
    for doc in result['source_documents']:
        source_name = os.path.basename(doc.metadata.get('source', 'Unknown'))
        print(f"- {source_name} (Page {doc.metadata.get('page', 'N/A')})")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_query = " ".join(sys.argv[1:])
    else:
        user_query = "What is the purpose of the Mifos platform?"

    query_mifos_ai(user_query)
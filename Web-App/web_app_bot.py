from dotenv import load_dotenv
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
import chromadb
import gradio as gr

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()

if not GOOGLE_API_KEY:
    raise EnvironmentError("Missing GOOGLE_API_KEY in environment variables.")

# --- File reading ---
def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def infer_module_name(file_path):
    parts = file_path.split(os.sep)
    return "/".join(parts[parts.index("src") + 1:-1]) if "src" in parts else "root"

# --- File processing ---
def process_files(root_dir, ext, language=None):
    splitter = RecursiveCharacterTextSplitter.from_language(language) if language else RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = []

    for root, _, files in os.walk(root_dir):
        for f in files:
            if f.endswith(ext):
                path = os.path.join(root, f)
                content = f"file name: {f}\n path: {infer_module_name(path)}\n {read_file(path)}"
                chunks = splitter.create_documents(
                    [content],
                    metadatas=[{
                        'source': f, 'type': ext[1:], 'module': infer_module_name(path), 'folder_path': root
                    }]
                )
                docs.extend(chunks)
    return docs

def process_all(root_dir):
    return sum([
        process_files(root_dir, '.ts', Language.TS),
        process_files(root_dir, '.html', Language.HTML),
        process_files(root_dir, '.txt'),
        process_files(root_dir, '.md'),
        process_files(root_dir, '.js', Language.JS)
    ], [])

# --- Vector DB init ---
def init_db():
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
    client = chromadb.PersistentClient(path="./web_app_vector_storage_metadata")
    name = "all_files"

    if os.path.exists("collection_storage.txt"):
        print("Loading existing vector DB...")
        return Chroma(client=client, collection_name=name, embedding_function=embeddings)
    else:
        print("Creating new vector DB...")
        docs = process_all("data_web_app")

        if not docs:
            raise ValueError("No files found in 'data_web_app'. Please ensure it contains valid source files.")

        print("Chunks:", len(docs))
        print("Files:", len(set([d.metadata['source'] for d in docs])))

        db = Chroma.from_documents(docs, embeddings, collection_name=name, client=client)
        with open("collection_storage.txt", "w") as f:
            f.write(f"{name}\n{client.list_collections()[0].id}")
        return db

# --- QA Chain ---
try:
    docsearch = init_db()
except Exception as e:
    print("❌ Error initializing vector DB:", e)
    exit(1)

llm = ChatGoogleGenerativeAI(model="models/gemini-1.5-flash", temperature=0.3, google_api_key=GOOGLE_API_KEY)
qa = RetrievalQA.from_chain_type(llm=llm, retriever=docsearch.as_retriever(), return_source_documents=True)

def answer_question(question):
    docs = docsearch.similarity_search_with_score(question, k=5)

    if not docs:
        return "😕 Sorry, I couldn't find anything relevant. Try rephrasing your question or ask about the project structure."

    context = "\n".join([doc.page_content for doc, _ in docs])
    prompt = (
        "You are an expert in project structure and code files (TS, HTML, etc). "
        "Focus on codebase layout, modules, and file paths. "
        "If unsure, suggest asking in the Mifos Slack. \n"
        f"Context:\n{context}\nQuestion: {question}"
    )
    response = qa.invoke(prompt)
    return response['result']

# --- Gradio UI ---
interface = gr.Interface(
    fn=answer_question,
    inputs=gr.Textbox(label="Ask a question about the Mifos Web-App"),
    outputs=gr.Textbox(label="Answer"),
    title="Mifos Web-App Chatbot (Gemini)",
    description="Ask anything about the structure and codebase."
)

if __name__ == "__main__":
    interface.launch(share=True)

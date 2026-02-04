import os
os.environ["OPENAI_API_KEY"] = "sk-proj-"
from llama_index.llms.cleanlab import CleanlabTLM
llm = CleanlabTLM(api_key="ea")
import pinecone

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores.pinecone import PineconeVectorStore
from IPython.display import Markdown, display
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from typing import Dict, List, ClassVar
from llama_index.core.instrumentation.events import BaseEvent
from llama_index.core.instrumentation.event_handlers import BaseEventHandler
from llama_index.core.instrumentation import get_dispatcher
from llama_index.core.instrumentation.events.llm import LLMCompletionEndEvent
Settings.llm = llm


Settings.embed_model = HuggingFaceEmbedding(
    model_name="nomic-ai/nomic-embed-text-v2-moe",
    trust_remote_code=True
)

import chromadb
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext

from llama_index.vector_stores.pinecone import PineconeVectorStore


pc = pinecone.Pinecone(api_key="Pinecone_API_Key")
index = pc.Index("mifos")
vector_store = PineconeVectorStore(pinecone_index=index)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

documents = SimpleDirectoryReader("./data").load_data()
index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
    embed_model=Settings.embed_model
)

class GetTrustworthinessScore(BaseEventHandler):
    events: ClassVar[List[BaseEvent]] = []
    trustworthiness_score: float = 0.0

    @classmethod
    def class_name(cls) -> str:
        """Class name."""
        return "GetTrustworthinessScore"

    def handle(self, event: BaseEvent) -> Dict:
        if isinstance(event, LLMCompletionEndEvent):
            self.trustworthiness_score = event.response.additional_kwargs[
                "trustworthiness_score"
            ]
            self.events.append(event)


root_dispatcher = get_dispatcher()

event_handler = GetTrustworthinessScore()
root_dispatcher.add_event_handler(event_handler)


def display_response(response):
    response_str = response.response
    trustworthiness_score = event_handler.trustworthiness_score
    print(f"Response: {response_str}")
    print(f"Trustworthiness score: {round(trustworthiness_score, 2)}")


chat_engine = index.as_chat_engine(
    chat_mode="openai",
    similarity_top_k=15,
    system_prompt="You are a helpful assistant that provides accurate information based on the documents provided.",
    verbose=False
)


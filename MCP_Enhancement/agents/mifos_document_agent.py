import os
import time
import logging
import requests
from typing import Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Project Imports
from MCP_Enhancement.config import get_settings
from MCP_Enhancement.scripts.ingest_docs import main as run_ingestion
from MCP_Enhancement.agents.rag_agent import query_docs

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MifosHybridAgent")


# --- PART 1: LIVE BANKING LOGIC (FineractAgent) ---

class FineractAgent:
    """
    Fetches live banking data from Mifos/Fineract.
    Aligned with the 'Knowledge Aggregator' goal: Read-only retrieval.
    """

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.FINERACT_BASE_URL
        self.tenant_id = self.settings.FINERACT_TENANT_ID
        self.auth = (self.settings.FINERACT_USERNAME, self.settings.FINERACT_PASSWORD)

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Fineract-Platform-TenantId": self.tenant_id,
            "Content-Type": "application/json",
        }

    def search_clients(self, display_name: str) -> str:
        """Search for live clients in the system."""
        endpoint = f"{self.base_url}/clients"
        params = {"displayName": display_name}
        try:
            logger.info(f"🔍 Searching Fineract API for: {display_name}")
            response = requests.get(endpoint, params=params, auth=self.auth, headers=self._get_headers(), timeout=10)
            if response.status_code == 200:
                clients = response.json().get("pageItems", [])
                if not clients: return f"ℹ️ No live clients found matching '{display_name}'."
                summary = [f"✅ Found {len(clients)} matches in Fineract:"]
                for c in clients[:3]:
                    summary.append(
                        f"- ID: {c.get('id')} | Name: {c.get('displayName')} | Office: {c.get('officeName')}")
                return "\n".join(summary)
            return f"❌ Fineract API Error: {response.status_code}"
        except Exception as e:
            return f"⚠️ Connection Failed: {str(e)}"

    def get_loan_details(self, client_id: int) -> str:
        """Fetch real-time loan status for a client."""
        endpoint = f"{self.base_url}/clients/{client_id}/accounts"
        try:
            response = requests.get(endpoint, auth=self.auth, headers=self._get_headers(), timeout=10)
            if response.status_code == 200:
                loans = response.json().get("loanAccounts", [])
                if not loans: return f"ℹ️ Client {client_id} has no live loans."
                summary = [f"🏦 Live Loan Portfolio for Client {client_id}:"]
                for l in loans:
                    status = l.get('status', {}).get('value', 'Unknown')
                    summary.append(
                        f"- Acct: {l.get('accountNo')} | Product: {l.get('productName')} | Balance: {l.get('loanBalance', 0)} | Status: {status}")
                return "\n".join(summary)
            return f"❌ Fineract API Error: {response.status_code}"
        except Exception as e:
            return f"⚠️ Connection Failed: {str(e)}"


# --- PART 2: DOCUMENT WATCHDOG LOGIC ---

class MifosDocHandler(FileSystemEventHandler):
    """Listens for file changes and triggers Pinecone ingestion."""

    def on_modified(self, event):
        if not event.is_directory and (event.src_path.endswith(('.md', '.pdf'))):
            logger.info(f"📄 Updating Pinecone for modified file: {event.src_path}")
            run_ingestion()

    def on_created(self, event):
        if not event.is_directory and (event.src_path.endswith(('.md', '.pdf'))):
            logger.info(f"🆕 Ingesting new file to Pinecone: {event.src_path}")
            run_ingestion()


def start_agent_services():
    """Starts the Watchdog and initializes the Fineract Agent."""
    path = "./MCP_Enhancement/docs"

    # Ensure directory exists before watching
    if not os.path.exists(path):
        os.makedirs(path)

    event_handler = MifosDocHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)

    logger.info("🚀 Mifos Hybrid Agent Started.")
    logger.info(f"📡 Watching for Docs in: {path}")
    logger.info("🏦 Fineract API Connection Ready.")

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    start_agent_services()
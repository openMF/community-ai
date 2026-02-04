import requests
import logging
from typing import Optional, Dict, Any

# Ensure this import matches your project structure
from MCP_Enhancement.config import get_settings

# Initialize logger
logger = logging.getLogger(__name__)


class FineractAgent:
    """
    A read-only agent responsible for fetching live banking data from the Mifos/Fineract backend.
    Aligned with the 'Knowledge Aggregator' goal: it retrieves status, it does not change state.
    """

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.fineract_base_url
        self.tenant_id = self.settings.fineract_tenant_id
        self.auth = (self.settings.fineract_username, self.settings.fineract_password)

    def _get_headers(self) -> Dict[str, str]:
        """Constructs standard headers for Fineract API calls."""
        return {
            "Fineract-Platform-TenantId": self.tenant_id,
            "Content-Type": "application/json",
            # "Accept": "application/json" # Optional but good practice
        }

    def search_clients(self, display_name: str) -> str:
        """
        Search for clients in the Mifos system by name.
        Useful for resolving 'Who is this issue affecting?' questions.
        """
        endpoint = f"{self.base_url}/clients"
        params = {"displayName": display_name}

        try:
            logger.info(f"🔍 Searching Fineract for client: {display_name}")
            response = requests.get(
                endpoint,
                params=params,
                auth=self.auth,
                headers=self._get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                clients = data.get("pageItems", [])

                if not clients:
                    return f"ℹ️ Fineract Search: No clients found matching '{display_name}'."

                # Format output for the AI to read easily
                summary = [f"✅ Found {len(clients)} match(es):"]
                for c in clients[:3]:  # Limit to top 3 to keep context window clean
                    summary.append(
                        f"- ID: {c.get('id')} | Name: {c.get('displayName')} | Office: {c.get('officeName')}")

                return "\n".join(summary)

            return f"❌ Fineract Error {response.status_code}: {response.text}"

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error in search_clients: {e}")
            return f"⚠️ Network Connection Failed: {str(e)}"

    def get_loan_details(self, client_id: int) -> str:
        """
        Fetches the loan portfolio for a specific client.
        Provides the 'context' needed for document production/status checks.
        """
        endpoint = f"{self.base_url}/clients/{client_id}/accounts"

        try:
            logger.info(f"🏦 Fetching loan accounts for Client ID: {client_id}")
            response = requests.get(
                endpoint,
                auth=self.auth,
                headers=self._get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                loans = data.get("loanAccounts", [])

                if not loans:
                    return f"ℹ️ Client ID {client_id} has no active loan accounts."

                summary = [f"🏦 Loan Portfolio for Client {client_id}:"]
                for l in loans:
                    # Safe extraction of nested keys
                    status = l.get('status', {}).get('value', 'Unknown')
                    summary.append(
                        f"- Acct: {l.get('accountNo')} | "
                        f"Product: {l.get('productName')} | "
                        f"Balance: {l.get('loanBalance', 0)} | "
                        f"Status: {status}"
                    )
                return "\n".join(summary)

            return f"❌ Fineract Error {response.status_code}: {response.text}"

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error in get_loan_details: {e}")
            return f"⚠️ Network Connection Failed: {str(e)}"


# Optional: Helper block for testing independently
if __name__ == "__main__":
    agent = FineractAgent()
    print(agent.search_clients("Test"))
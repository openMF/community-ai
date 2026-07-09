import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

db = None # Global Firestore client instance

async def initialize_firestore():
    """
    Initializes the Firestore client. This function should be called once on application startup.
    It's safe to call this multiple times.
    """
    global db
    if db is not None:
        return

    try:
        if not firebase_admin._apps:
            if os.environ.get('__firebase_config'):
                firebase_config = json.loads(os.environ['__firebase_config'])
                cred = credentials.Certificate(firebase_config)
                firebase_admin.initialize_app(cred)
                logger.info("Firestore initialized using __firebase_config (Canvas environment).")
            else: 
                project_id = os.getenv("FIRESTORE_PROJECT_ID")
                key_path = os.getenv("FIRESTORE_SERVICE_ACCOUNT_PATH")
                if not project_id or not key_path:
                    logger.warning("Firestore .env variables not found. Banking features will be disabled.")
                    return
                if not os.path.exists(key_path):
                    raise FileNotFoundError(f"Firestore service account key not found at: {key_path}")
                
                cred = credentials.Certificate(key_path)
                firebase_admin.initialize_app(cred, {'projectId': project_id})
                logger.info("Firestore initialized using service account key (local development).")

        db = firestore.client()
        logger.info("Firestore client successfully initialized.")
    except Exception as e:
        logger.error(f"FATAL: Failed to initialize Firestore: {e}")
        db = None
        raise

def get_current_user_id(username: str = None) -> str:
    """
    Generates a consistent user ID.
    """
    if username:
        return f"local_user_{username.lower().replace(' ', '_')}"
    
    app_id = os.environ.get('__app_id', 'default-app-id')
    if os.environ.get('__initial_auth_token'):
        return f"canvas_user_{app_id}"
    else:
        return "local_test_user_123"

def _get_user_doc_ref(user_id: str):
    """Internal helper to get a reference to a user's main document."""
    app_id = os.getenv("__app_id", "default-app-id")
    return db.collection("artifacts").document(app_id).collection("users").document(user_id)

# --- User Profile & Account Creation ---

async def set_user_profile(user_id: str, data: dict):
    """Sets or updates a user's profile data on the user document itself."""
    if not db: return
    user_doc_ref = _get_user_doc_ref(user_id)
    await asyncio.to_thread(user_doc_ref.set, data, merge=True)

async def create_or_update_account(user_id: str, account_number: str, account_data: dict):
    """Creates or updates a specific banking account in a sub-collection."""
    if not db: return
    user_doc_ref = _get_user_doc_ref(user_id)
    account_ref = user_doc_ref.collection("accounts").document(account_number)
    await asyncio.to_thread(account_ref.set, account_data, merge=True)

async def update_account_balance(user_id: str, account_number: str, new_balance: float):
    """Updates the balance of a specific banking account."""
    if not db: return
    user_doc_ref = _get_user_doc_ref(user_id)
    account_ref = user_doc_ref.collection("accounts").document(account_number)
    await asyncio.to_thread(account_ref.update, {"balance": new_balance})

async def debit_account_atomic(user_id: str, account_number: str, amount: float) -> str:
    """
    Atomically debits `amount` from an account inside a Firestore transaction.
    Returns "success" if debited, "insufficient_funds" if the balance is too low,
    and "not_found" if the account does not exist.
    """
    if not db: return "not_found"
    user_doc_ref = _get_user_doc_ref(user_id)
    account_ref = user_doc_ref.collection("accounts").document(account_number)

    def _debit():
        transaction = db.transaction()

        @firestore.transactional
        def _update_in_transaction(transaction):
            snapshot = account_ref.get(transaction=transaction)
            if not snapshot.exists:
                return "not_found"
            balance = snapshot.to_dict().get("balance", 0)
            if balance < amount:
                return "insufficient_funds"
            transaction.update(account_ref, {"balance": balance - amount})
            return "success"

        return _update_in_transaction(transaction)

    return await asyncio.to_thread(_debit)

async def add_transaction(user_id: str, account_number: str, transaction_data: dict) -> str | None:
    """Adds a new transaction to a specific banking account."""
    if not db: return None
    user_doc_ref = _get_user_doc_ref(user_id)
    transactions_ref = user_doc_ref.collection("accounts").document(account_number).collection("transactions")
    update_time, doc_ref = await asyncio.to_thread(transactions_ref.add, transaction_data)
    return doc_ref.id

# --- Data Retrieval Operations ---

# NEW FUNCTION
async def get_user_account(user_id: str, account_number: str) -> dict | None:
    """Fetches a specific banking account for a user."""
    if not db: return None
    user_doc_ref = _get_user_doc_ref(user_id)
    
    def _get_doc():
        account_ref = user_doc_ref.collection("accounts").document(account_number)
        doc = account_ref.get()
        return doc.to_dict() if doc.exists else None
    
    return await asyncio.to_thread(_get_doc)

# NEW FUNCTION
async def get_all_user_accounts(user_id: str) -> list[dict]:
    """Fetches all banking accounts for a user."""
    if not db: return []
    user_doc_ref = _get_user_doc_ref(user_id)

    def _get_docs():
        accounts_ref = user_doc_ref.collection("accounts")
        docs = accounts_ref.stream()
        return [doc.to_dict() for doc in docs]

    return await asyncio.to_thread(_get_docs)

async def get_all_user_accounts_summary(user_id: str) -> list[dict]:
    """
    Fetches a summarized list of all banking accounts for a user,
    containing only account_number, type, and balance.
    """
    user_doc_ref = _get_user_doc_ref(user_id)
    if not user_doc_ref: 
        return []

    def _get_docs():
        accounts_ref = user_doc_ref.collection("accounts")
        docs = accounts_ref.stream()
        
        # Create a list of smaller dictionaries with only the required fields
        summary_list = []
        for doc in docs:
            full_data = doc.to_dict()
            summary_data = {
                "account_number": doc.id,
                "type": full_data.get("type"),
                "balance": full_data.get("balance")
            }
            summary_list.append(summary_data)
        return summary_list

    return await asyncio.to_thread(_get_docs)

async def get_user_transactions(user_id: str, account_number: str, limit: int = 20) -> list[dict]:
    """Fetches recent transactions for a specific banking account."""
    if not db: return []
    user_doc_ref = _get_user_doc_ref(user_id)
    transactions_ref = user_doc_ref.collection("accounts").document(account_number).collection("transactions")
    
    query = transactions_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
    docs = await asyncio.to_thread(query.get)

    return [doc.to_dict() for doc in docs]
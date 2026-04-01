import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()
logger = logging.getLogger(__name__)

model = None
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    # --- THIS IS THE CHANGE ---
    # Relax the setting for this category to prevent false positives on financial talk
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]

# --- NEW: A single, powerful base prompt for our assistant's persona and rules ---
BASE_SYSTEM_PROMPT = """
You are a warm, professional, and helpful voice banking assistant. 
Your primary task is to generate a brief, conversational response suitable for being spoken aloud, based on the context provided.

## CRITICAL RESPONSE RULES ##
1.  **Language and Script**: You MUST respond ONLY in the language and native script specified by the 'Target Language Code'. (e.g., for Hindi 'hi', use Devanagari script). NEVER mix languages or scripts.
2.  **Numbers to Words**: For clarity in speech, you MUST write out all numbers, especially monetary amounts. (e.g., 'five hundred twenty-five rupees and fifty paise', not '₹525.50').
3.  **Brevity**: Keep responses short and to the point.
SOme point keep in mind :
- When presenting numbers, especially monetary amounts, you MUST write them out in words (e.g., 'five hundred rupees' instead of '₹500', 'one thousand eight hundred twenty' instead of '1820'). This is for a Text-to-Speech engine.
-  If the intent is 'unknown' or 'fallback_unsupported', you MUST politely decline to answer non-banking questions and gently guide the user back to banking topics. Do not answer questions about weather, news, or general knowledge.
-  If the intent is 'goodbye' or a closing remark, respond warmly and end the conversation professionally. Example: "Thank you for using our service. Have a great day!"
- when you checking balanace always tell balance with account number and account type, like "Your savings account ending with 1234 has a balance of five thousand rupees."
- when you list transactions always tell account number and account type, like "Here are the last five transactions for your savings account ending with 1234."
- when you have data of transaction you have check the all data and found type as credit and debit , " here is you last debit transaction detail for your savings account ending with 1234, on 15th August 2025, you spent five hundred rupees at XYZ Store.


## BEHAVIORAL RULES based on INTENT ##
- **list_transactions**: Provide a concise summary of recent transactions, including date, amount (in words), type (credit/debit), and merchant. Example: "Here are your last five transactions only reposne most 2-3 and said rest on the scrren : On August fifteenth, you spent five hundred rupees at XYZ Store; on August fourteenth, you received one thousand rupees from ABC CorABC and rest you can see on the screen."
- **greeting**: Provide a friendly, professional opening and offer assistance suggestion the query you an ask me realted loan , balance cheking , trnasfer money and transaction related query , give example for better understanding .
- **goodbye / action_cancelled**: End the conversation warmly and professionally. Example: "Thank you for using our service. Have a great day! and suggetsome query example "What is my account balance?" or "List my last 5 transactions and transfer money and loan realted query"
- **unknown / fallback_unsupported**: NEVER invent answers for non-banking topics. Politely state your purpose and suggest valid commands. Example: "I can only assist with banking questions, such as asking for your balance or listing recent transactions , example "What is my account balance?" or "List my last 5 transactions and transfer money and loan realted query"
- **request_otp**: Inform the user clearly and professionally that a security code has been sent to their registered email address for verification , you can say like " otp is 123456 ".
- **error_otp_incorrect**: State clearly that the code was incorrect. Ask them to please try again, phrasing it in a way that suggests a slower, clearer speaking pace for the TTS. Example: "That code is not correct. Please... try... again with correct otp check email for otp "
- **transfer_success**: Give a clear, positive confirmation that the transfer was successful ,please contact your recipient that he recived or not thank you for using our service and you can ask example: waht is my account balance?" or "List my last 5 transactions and transfer money and loan realted query"
- **confirm_transfer**: Clearly summarize the transfer details (amount, recipient, account type) and ask for confirmation before proceeding. Example: "You are transferring five thousand rupees to John Doe from your savings account. Is that correct? otherwise , please spell the name to whow you want to transfer money.
"""

try:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in .env file.")
    
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        safety_settings=safety_settings,
        system_instruction=BASE_SYSTEM_PROMPT # Set the base instructions for the model
    )
    logger.info("Gemini model 'gemini-1.5-flash' initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize Gemini: {e}", exc_info=True)

def json_serial_default(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def _format_history(history: list) -> str:
    """Format conversation history into a readable string for the LLM."""
    if not history:
        return "No previous conversation."
    
    formatted = []
    for msg in history:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        formatted.append(f"{role}: {content}")
    
    return "\n".join(formatted[-5:])  # Only use last 5 turns to keep context manageable

async def get_llm_nlu_response(prompt: str) -> str | None:
    # This function remains the same, it doesn't need the system prompt
    if not model: return None
    try:
        # Create a separate model instance for NLU without the system prompt
        nlu_model = genai.GenerativeModel(model_name="gemini-2.5-flash")
        config = {"temperature": 0.1, "response_mime_type": "application/json"}
        response = await nlu_model.generate_content_async(prompt, generation_config=config, safety_settings=safety_settings)
        return response.text
    except Exception as e:
        logger.error(f"An error occurred during NLU call: {e}", exc_info=True)
        return None

async def get_llm_final_response(user_query: str, db_context: dict, language: str, history: list = None) -> str | None:
    """Generates a data-driven response using the conversation history for context."""
    if not model: return None
    try:
        context_string = json.dumps(db_context, default=json_serial_default)
        history_context = _format_history(history or [])
        
        prompt_parts = [
            "## TASK ##",
            f"Previous Conversation:\n{history_context}",
            "---",
            f"Target Language Code: {language}",
            f"Data from Database: {context_string}",
            f"User's New Query: {user_query}",
            "---",
            "Your Spoken Response:"
        ]
        
        config = {"temperature": 0.7}
        response = await model.generate_content_async(prompt_parts, generation_config=config)
        return response.text.strip()
    except Exception as e:
        logger.error(f"An error occurred during final response generation: {e}", exc_info=True)
        return None

async def generate_static_response(intent: str, language: str, user_query: str, history: list = None) -> str | None:
    """Generates a conversational response, using history for context."""
    if not model: return None
    try:
        history_context = _format_history(history or [])
        
        prompt_parts = [
            "## TASK ##",
            f"Previous Conversation:\n{history_context}",
            f"Target Language Code: {language}",
            f"Situation (Intent): {intent}",
            f"User's New Query: {user_query}",
            "---",
            "Your Spoken Response:"
        ]
        
        config = {"temperature": 0.7}
        response = await model.generate_content_async(prompt_parts, generation_config=config)
        return response.text.strip()
    except Exception as e:
        logger.error(f"An error occurred during static response generation: {e}", exc_info=True)
        return "I'm sorry, I encountered an error."

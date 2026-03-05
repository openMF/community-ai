# backend/main.py    uvicorn main:app --reload

import logging
import sys
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import base64
import os
import uuid
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

from services import sarvam_stt, sarvam_tts, intent_nlu, firestore_db, firestore_session
from services.llm_gemini import get_llm_final_response, generate_static_response
from models.audio_models import AudioInput
from models.api_models import ConverseResponse
from fastapi.middleware.cors import CORSMiddleware
from services.eamil_services import send_otp_email
import random

# A more robust logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log", mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# A dictionary for language codes is cleaner and more correct
TTS_LANGUAGE_MAP = {
    "en": "en-IN", 
    "hi": "hi-IN",
    "pa": "pa-IN",
    "bn": "bn-IN",
    "gu": "gu-IN",
    "mr": "mr-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "ml": "ml-IN",
    "kn": "kn-IN",
    "or": "od-IN"
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Server starting up...")
    # Sarvam APIs don't need local model initialization like Whisper did
    await firestore_db.initialize_firestore()
    if firestore_db.db is None:
        raise RuntimeError("FATAL: Firestore database connection failed.")
    logger.info("All services initialized.")
    yield
    logger.info("Server shutting down...")

app = FastAPI(lifespan=lifespan)

# Add CORS Middleware
origins = ["http://localhost", "http://localhost:3000"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/", summary="Health Check")
def read_root():
    return {"status": "ok", "message": "Welcome to the Voice Banking API"}

@app.post("/converse", response_model=ConverseResponse)
async def converse(audio_input: AudioInput):
    request_id = uuid.uuid4()
    temp_audio_path = f"temp_{request_id}_input.wav"
    output_audio_path = f"temp_{request_id}_response.wav"
    
    try:
        # 1. Decode Base64 audio and save
        audio_data = base64.b64decode(audio_input.audio_data)
        with open(temp_audio_path, "wb") as f: f.write(audio_data)

        # 2. STT (Sarvam Saaras)
        user_text = sarvam_stt.transcribe_audio_file(temp_audio_path, language=audio_input.language)
        if not user_text: raise HTTPException(status_code=400, detail="Could not understand audio.")
        logger.info(f"Transcribed Text: {user_text}")

        # 3. NLU
        nlu_result = await intent_nlu.get_intent_and_entities(user_text)
        if not nlu_result: raise HTTPException(status_code=500, detail="NLU processing failed.")
        
        intent = nlu_result.get("intent")
        entities = nlu_result.get("entities", {})
        logger.info(f"Detected Intent: '{intent}', Entities: {entities}")

        # 4. Get Session Context
        user_id = "local_user_vickey_kumar"
        session_id = audio_input.session_id
        session_data = await firestore_session.get_sessionid_history(session_id, user_id)
        conversation_history = session_data.get("messages", [])
        logger.info(f"Session Data Retrieved: {session_data}")
        pending_action = session_data.get("pending_action")
        logger.info(f"Pending Action: {pending_action}")

        response_text = ""
        response_data = None

        # --- STATE MACHINE LOGIC ---
        if pending_action:
            if pending_action.get("type") == "transfer_confirmation" and intent == "confirm_action":
                otp = str(random.randint(100000, 999999))
                send_otp_email("vkkumar1763@gmail.com", otp)
                response_text = await generate_static_response(
                    "request_otp we have send to your email",
                    audio_input.language,
                    user_text,
                    history=conversation_history
                )
                pending_action["type"] = "otp_verification"
                pending_action["otp"] = otp
            
            elif pending_action.get("type") == "otp_verification" and intent == "inform_otp":
                provided_otp = entities.get("otp_code", "").replace(" ", "")

                if provided_otp == pending_action.get("otp"):
                    # OTP is correct - execute the transfer
                    amount = pending_action.get("amount")
                    recipient = pending_action.get("recipient", "recipient")
                    source_account_number = pending_action.get("source_account_number")
                    
                    source_account = await firestore_db.get_user_account(user_id, source_account_number)
                    
                    if source_account and source_account.get('balance', 0) >= amount:
                        new_balance = source_account['balance'] - amount
                        await firestore_db.update_account_balance(user_id, source_account_number, new_balance)
                        
                        debit_transaction = {
                            "date": datetime.now(),
                            "description": f"Transfer to {recipient}",
                            "amount": -amount,
                            "type": "debit",
                            "category": "Transfer",
                            "timestamp":  datetime.now()
                            }
                        
                        await firestore_db.add_transaction(user_id, source_account_number, debit_transaction)
                        response_text = await generate_static_response("transfer_success", audio_input.language, user_text)
                        pending_action = None
                    else:
                        response_text = await generate_static_response("error_insufficient_funds", audio_input.language, user_text)
                        pending_action = None
                else:
                    response_text = await generate_static_response("error_otp_incorrect", audio_input.language, user_text)
            
            elif pending_action.get("type") == "transfer_confirmation" and intent == "cancel_action":
                response_text = await generate_static_response(
                    "action_cancelled",
                    audio_input.language,
                    user_text,
                    history=conversation_history
                )
                pending_action = None
            
            else:
                response_text = await generate_static_response(
                    "action_in_progress",
                    audio_input.language,
                    user_text,
                    history=conversation_history
                )

        elif intent == "transfer_money":
            amount = entities.get("amount")
            recipient = entities.get("recipient")

            if not amount or not recipient:
                response_text = await generate_static_response("missing_transfer_details", audio_input.language, user_text , history=conversation_history)
            else:
                all_accounts = await firestore_db.get_all_user_accounts_summary(user_id)
                source_account = next((acc for acc in all_accounts if acc.get("type", "").lower() == "savings"), None)
                
                if source_account:
                    response_text = await generate_static_response(
                        "confirm_transfer",
                        audio_input.language,
                        user_text, 
                        history=conversation_history
                    )
                    pending_action = {
                        "type": "transfer_confirmation",
                        "amount": amount,
                        "recipient": recipient,
                        "source_account_number": source_account.get("account_number")
                    }
                else:
                    response_text = await generate_static_response(
                        "error_no_savings_account",
                        audio_input.language,
                        user_text, 
                        history=conversation_history
                    )
            
        # 5. Business Logic
        elif intent == "check_balance":
            account_data = await firestore_db.get_all_user_accounts(user_id)
            #if entities is blank or not entities.get("account_type"):
            if not entities or not entities.get("account_type"):
                response_text = await generate_static_response(
                    "Ask for account_type",
                    audio_input.language,
                    user_text,
                    history=conversation_history
                )
            
            if account_data:
                logger.info(f"Account data retrieved: {account_data}")
                if entities.get("account_type") == "saving"  or entities.get("account_type") == "savings":
                    response_text = await get_llm_final_response(
                        user_query=user_text + " for savings account",
                        db_context={"accounts_summary": account_data}, # Pass the list of accounts
                        language=audio_input.language,
                        history=conversation_history
                )
                elif entities.get("account_type") == "current":
                    response_text = await get_llm_final_response(
                        user_query=user_text + " for current account",
                        db_context={"accounts_summary": account_data}, # Pass the list of
                        language=audio_input.language,
                        history=conversation_history
                )
            else:
                response_text = await generate_static_response(
                    "error_no_account",
                    audio_input.language,
                    user_text,
                    history=conversation_history
                )

       # In main.py, inside the /converse endpoint

        elif intent == "list_transactions":
            # 1. Get entities from NLU, with defaults
            limit = entities.get("limit", 10)
            target_account_type = entities.get("account_type", "").lower()
            # print(f"Limit: {limit}, Target Account Type: {target_account_type}")
            # 2. Fetch all available accounts for the user
            all_accounts = await firestore_db.get_all_user_accounts_summary(user_id)
            # print(f"All Accounts: {all_accounts}")
            target_account_number = None
            
            # 3. Find the matching account number based on the user's request
            if target_account_type:
                # If user specified an account type (e.g., "savings")
                for acc in all_accounts:
                    if acc.get("type", "").lower() == target_account_type or acc.get("type", "").lower() == "savings":
                        target_account_number = acc.get("account_number")
                        break
            elif len(all_accounts) == 1:
                # If user did not specify, but they only have one account
                target_account_number = all_accounts[0].get("account_number")

            # 4. Now, either fetch transactions or ask for clarification
            if target_account_number:
                # We found the account number, so get its transactions
                transactions = await firestore_db.get_user_transactions(user_id, target_account_number, limit=limit)
                logger.info(f"Transactions for account {target_account_number}: {transactions}")
                if transactions:
                
                    response_text = await get_llm_final_response(
                        user_query=user_text, 
                        db_context={"transactions_summary": transactions}, 
                        language=audio_input.language,
                        history=conversation_history
                    )
                    response_data = {"transactions": transactions} # Full list for UI
                else:
                    response_text = await generate_static_response("error_no_transactions", audio_input.language, user_text, history=conversation_history)
            
            elif len(all_accounts) > 1:
                # User has multiple accounts but didn't specify which one
                response_text = await get_llm_final_response(
                    user_query=user_text, 
                    db_context={"accounts": all_accounts}, 
                    language=audio_input.language,
                    history=conversation_history
                )
            else:
                # User has no accounts at all
                 response_text = await generate_static_response("error_no_account", audio_input.language, user_text, history=conversation_history)
        
        # ... (after the full if/elif/else block for intents)
        elif intent == "greeting":
            response_text = await generate_static_response(
                "greeting",
                audio_input.language,
                user_text,
                history=conversation_history
            )
        else:
            response_text = await generate_static_response(
                "fallback",
                audio_input.language,
                user_text,
                history=conversation_history
            )

        # In the return statement at the end of the function, pass the data
        if not response_text: raise HTTPException(status_code=500, detail="Failed to generate text response.")
        logger.info(f"Generated Response Text: {response_text}")

        # 5. Session Update (moved before slow TTS call)
        if session_id:
            await firestore_session.append_to_session(session_id, user_id, user_text, response_text, pending_action=pending_action)

        # 6. TTS (Sarvam Bulbul)
        tts_language = audio_input.language # sarvam_tts handles the precise mapping internally or here
        if tts_language not in TTS_LANGUAGE_MAP:
            logger.warning(f"Unsupported language for TTS: {audio_input.language}, falling back to en-IN")
            tts_language = "en"
        
        # FIX: Check if the TTS service succeeded before trying to read the file
        tts_result_path = await sarvam_tts.generate_speech(text=response_text, language=tts_language, output_file=output_audio_path)
        if not tts_result_path:
            raise HTTPException(status_code=500, detail="Failed to generate speech audio.")

        # 7. Encode and Return Audio
        with open(output_audio_path, "rb") as audio_file:
            encoded_audio_data = base64.b64encode(audio_file.read()).decode('utf-8')
        return ConverseResponse(
            user_text=user_text,
            response_text=response_text,
            audio_data=encoded_audio_data,
            data=response_data # <-- Pass the full transaction list here
        )

    except Exception as e:
        logger.error(f"An error in the conversation pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred.")
    finally:
        # 8. Clean up temporary files
        if os.path.exists(temp_audio_path): os.remove(temp_audio_path)
        if os.path.exists(output_audio_path): os.remove(output_audio_path)
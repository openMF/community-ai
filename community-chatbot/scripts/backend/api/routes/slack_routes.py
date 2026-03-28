from fastapi import APIRouter, HTTPException
from backend.models.schemas import ChatRequest, ChatResponse, ConversationHistoryResponse, ChatMessageSchema
from backend.core.state import slack_store
from backend.services.slack_service import get_slack_agent

router = APIRouter(tags=["slack"])

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        session_id = request.session_id
        
        # Get or create agent
        agent = slack_store.get_agent(session_id)
        if not agent:
            agent = get_slack_agent()
            slack_store.set_agent(session_id, agent)

        slack_store.add_message(session_id, ("user", request.message))
        chat_history = slack_store.get_session(session_id)
        
        events = agent.stream({"messages": chat_history}, stream_mode="values")
        
        final_response = ""
        final_event = None
        
        for event in events:
            final_event = event
            message = event["messages"][-1]
            if hasattr(message, 'content') and message.type == "ai":
                if not (hasattr(message, 'tool_calls') and message.tool_calls):
                    final_response = message.content
                    
        if final_event:
            slack_store.update_session(session_id, final_event["messages"])
            
        if not final_response:
            final_response = "I processed your request, but didn't generate a text response."
            
        return ChatResponse(response=str(final_response), session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{session_id}", response_model=ConversationHistoryResponse)
async def get_conversation(session_id: str):
    history = slack_store.get_session(session_id)
    formatted = []
    
    for message in history:
        if hasattr(message, 'type') and hasattr(message, 'content'):
            formatted.append(ChatMessageSchema(role=message.type, content=str(message.content)))
        elif isinstance(message, tuple) and len(message) == 2:
            formatted.append(ChatMessageSchema(role=message[0], content=str(message[1])))
        else:
            formatted.append(ChatMessageSchema(role="unknown", content=str(message)))
            
    return ConversationHistoryResponse(session_id=session_id, messages=formatted)

@router.delete("/conversations/{session_id}")
async def clear_conversation(session_id: str):
    slack_store.clear_session(session_id)
    return {"message": f"Conversation {session_id} cleared"}

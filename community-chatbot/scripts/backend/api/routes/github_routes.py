from fastapi import APIRouter, HTTPException
from backend.models.schemas import ChatRequest, ChatResponse
from backend.core.state import github_store
from backend.services.github_service import get_github_agent

router = APIRouter(tags=["github"])

@router.post("/chat", response_model=ChatResponse)
async def chat_with_github_agent(request: ChatRequest):
    try:
        agent_executor = get_github_agent()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent not initialized: {e}")
        
    session_id = request.session_id
    user_message = request.message
    
    # Add user message to state
    github_store.add_message(session_id, ("user", user_message))
    chat_history = github_store.get_session(session_id)
    
    try:
        events = agent_executor.stream(
            {"messages": chat_history},
            stream_mode="values"
        )
        
        last_msg = None
        for event in events:
            last_msg = event["messages"][-1]
            
        if last_msg:
            response_content = last_msg.content
            github_store.add_message(session_id, ("assistant", response_content))
        else:
            response_content = "Sorry, I couldn't process your request."
            
        return ChatResponse(response=response_content, session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@router.get("/sessions")
async def get_sessions():
    return {"sessions": github_store.get_all_session_ids()}

@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    if github_store.clear_session(session_id):
        return {"message": f"Session {session_id} cleared"}
    raise HTTPException(status_code=404, detail="Session not found")

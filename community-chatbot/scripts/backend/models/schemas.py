from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Generic Chat Models (used by GitHub and Slack)
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    session_id: str

# Jira Specific Models
class JiraQueryRequest(BaseModel):
    query: str
    use_fallback: bool = True 

class JiraQueryResponse(BaseModel):
    response: str
    query_used: str
    method_used: str 
    success: bool
    
# Conversation History Models (used by Slack endpoint GET /conversations/{id})
class ChatMessageSchema(BaseModel):
    role: str
    content: str

class ConversationHistoryResponse(BaseModel):
    session_id: str
    messages: List[ChatMessageSchema]

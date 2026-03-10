from typing import Dict, List, Any
from threading import Lock

class MemoryStore:
    """Thread-safe in-memory store for chat sessions and agents."""
    def __init__(self):
        self._chat_sessions: Dict[str, List[Any]] = {}
        self._agents: Dict[str, Any] = {}
        self._lock = Lock()

    def get_session(self, session_id: str) -> List[Any]:
        with self._lock:
            if session_id not in self._chat_sessions:
                self._chat_sessions[session_id] = []
            return list(self._chat_sessions[session_id]) # Return a shallow copy

    def update_session(self, session_id: str, messages: List[Any]):
        with self._lock:
            self._chat_sessions[session_id] = messages

    def add_message(self, session_id: str, message: Any):
        with self._lock:
            if session_id not in self._chat_sessions:
                self._chat_sessions[session_id] = []
            self._chat_sessions[session_id].append(message)

    def clear_session(self, session_id: str) -> bool:
        with self._lock:
            popped = False
            if session_id in self._chat_sessions:
                del self._chat_sessions[session_id]
                popped = True
            if session_id in self._agents:
                del self._agents[session_id]
            return popped

    def get_agent(self, session_id: str) -> Any:
        with self._lock:
            return self._agents.get(session_id)

    def set_agent(self, session_id: str, agent: Any):
        with self._lock:
            self._agents[session_id] = agent

    def delete_agent(self, session_id: str):
        with self._lock:
            if session_id in self._agents:
                del self._agents[session_id]

    def get_all_session_ids(self) -> List[str]:
        with self._lock:
            return list(self._chat_sessions.keys())

# Global stores
github_store = MemoryStore()
slack_store = MemoryStore()

import importlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from langchain_core.messages import (
    BaseMessage,
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    ChatMessage,
    FunctionMessage
)

from .utils import truthy


__all__ = ["RuntimeState", "MESSAGE_TYPE_REGISTRY"]


_STATE_FILE_ENV = "MCP_STATE_FILE"
_STATE_DIR_ENV = "MCP_STATE_DIR"
_STATE_DISABLE_ENV = "MCP_DISABLE_PERSISTENCE"
_DEFAULT_STATE_FILENAME = "mcp_sessions.json"
_DEFAULT_STATE_SUBDIR = ".mcp"

MESSAGE_TYPE_REGISTRY: dict[str, type[BaseMessage]] = {
    "ai": AIMessage,
    "human": HumanMessage,
    "system": SystemMessage,
    "tool": ToolMessage,
}
for key, cls in (("function", FunctionMessage), ("chat", ChatMessage)):
    if key not in MESSAGE_TYPE_REGISTRY and cls is not None:
        MESSAGE_TYPE_REGISTRY[key] = cast(type[BaseMessage], cls)


def _persistence_disabled() -> bool:
    return truthy(os.getenv(_STATE_DISABLE_ENV))


def _resolve_state_file_path(service_name: str = "mcp") -> Path:
    if _persistence_disabled():
        return Path(os.devnull)

    configured_file = os.getenv(_STATE_FILE_ENV)
    if configured_file:
        path = Path(configured_file).expanduser()
    else:
        base_dir = os.getenv(_STATE_DIR_ENV)
        if base_dir:
            base_path = Path(base_dir).expanduser()
        else:
            base_path = Path.home() / _DEFAULT_STATE_SUBDIR
        path = base_path / f"{service_name}_sessions.json"

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"Unable to prepare state directory: {exc}", file=sys.stderr)
    return path


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _serialize_message(message: BaseMessage) -> dict[str, Any]:
    try:
        data = json.loads(message.json())
    except (AttributeError, ValueError, TypeError):
        if hasattr(message, "dict"):
            data = cast(Any, message).dict()
        else:
            data = {"content": getattr(message, "content", "")}
    data.pop("type", None)
    return {
        "type": message.type,
        "class_path": (
            f"{message.__class__.__module__}."
            f"{message.__class__.__name__}"
        ),
        "data": data,
    }


def _locate_message_class(class_path: str) -> type[BaseMessage] | None:
    module_name, _, class_name = class_path.rpartition(".")
    if not module_name or not class_name:
        return None
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return None
    candidate = getattr(module, class_name, None)
    return cast(type[BaseMessage], candidate) if isinstance(candidate, type) and issubclass(candidate, BaseMessage) else None


def _deserialize_message(payload: dict[str, Any]) -> BaseMessage | None:
    message_type = payload.get("type")
    data = payload.get("data") or {}
    if not isinstance(data, dict):
        return None
    message_cls = (
        MESSAGE_TYPE_REGISTRY.get(message_type)
        if isinstance(message_type, str)
        else None
    )
    if message_cls is None:
        class_path = payload.get("class_path")
        if isinstance(class_path, str):
            message_cls = _locate_message_class(class_path)
    if message_cls is None:
        return None

    data = data.copy()
    data.pop("type", None)
    try:
        return message_cls(**data)
    except (TypeError, ValueError):
        return message_cls(content=data.get("content", ""))


class RuntimeState:
    """Holds runtime information shared across CLI commands."""

    def __init__(self, service_name: str = "mcp") -> None:
        self.service_name = service_name
        self.agent_executor: Any = None
        self.mcp_client: Any | None = None
        self.chat_sessions: dict[str, list[BaseMessage]] = {}
        self.session_metadata: dict[str, dict[str, Any]] = {}
        self.tool_summaries: list[dict[str, object]] = []
        self.tool_map: dict[str, Any] = {}
        self.tool_details: dict[str, dict[str, Any]] = {}
        self.persistence_enabled: bool = not _persistence_disabled()
        self.state_file_path: Path = _resolve_state_file_path(service_name)
        if self.persistence_enabled:
            self._load_persisted_sessions()

    def record_message(
        self,
        session_id: str,
        message: BaseMessage,
    ) -> list[BaseMessage]:
        history = self._ensure_session(session_id)
        history.append(message)
        self._touch_session(session_id, persist=True)
        return history

    def pop_last_message(self, session_id: str) -> None:
        history = self.chat_sessions.get(session_id)
        if not history:
            return
        history.pop()
        if history:
            self._touch_session(session_id, persist=True)
            return
        self.clear_session(session_id, persist=True)

    def clear_session(self, session_id: str, *, persist: bool = False) -> None:
        self.chat_sessions.pop(session_id, None)
        self.session_metadata.pop(session_id, None)
        if persist and self.persistence_enabled:
            self._persist_sessions()

    def serialize_session(self, session_id: str) -> dict[str, Any] | None:
        history = self.chat_sessions.get(session_id)
        if history is None:
            return None
        metadata = self.session_metadata.get(session_id, {})
        return {
            "session_id": session_id,
            "metadata": {
                "created_at": metadata.get("created_at"),
                "updated_at": metadata.get("updated_at"),
                "message_count": len(history),
            },
            "messages": [_serialize_message(m) for m in history],
        }

    def list_sessions(self) -> list[dict[str, Any]]:
        sessions = [
            {
                "session_id": sid,
                "message_count": len(hist),
                "created_at": (
                    self.session_metadata.get(sid, {})
                    .get("created_at")
                ),
                "updated_at": (
                    self.session_metadata.get(sid, {})
                    .get("updated_at")
                ),
            }
            for sid, hist in self.chat_sessions.items()
        ]
        sessions.sort(
            key=lambda item: item.get("updated_at") or "",
            reverse=True,
        )
        return sessions

    def _ensure_session(self, session_id: str) -> list[BaseMessage]:
        history = self.chat_sessions.setdefault(session_id, [])
        if not history:
            now = _utc_timestamp()
            self.session_metadata[session_id] = {
                "created_at": now,
                "updated_at": now,
                "message_count": 0,
            }
            self._persist_sessions()
        return history

    def _touch_session(self, session_id: str, *, persist: bool) -> None:
        metadata = self.session_metadata.setdefault(session_id, {})
        metadata.setdefault("created_at", _utc_timestamp())
        metadata["updated_at"] = _utc_timestamp()
        metadata["message_count"] = len(self.chat_sessions.get(session_id, []))
        if persist and self.persistence_enabled:
            self._persist_sessions()

    def _load_persisted_sessions(self) -> None:
        if not self.persistence_enabled:
            return
        path = self.state_file_path
        if not path.exists():
            return
        try:
            raw = path.read_text(encoding="utf-8")
            payload = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            print(
                f"Failed to load persisted chat sessions: {exc}",
                file=sys.stderr,
            )
            return

        sessions = payload.get("sessions")
        if not isinstance(sessions, dict):
            return

        for session_id, record in sessions.items():
            if not isinstance(session_id, str) or not isinstance(record, dict):
                continue
            messages_payload = record.get("messages", [])
            if not isinstance(messages_payload, list):
                messages_payload = []
            history: list[BaseMessage] = []
            for message_payload in messages_payload:
                if not isinstance(message_payload, dict):
                    continue
                message = _deserialize_message(message_payload)
                if message is not None:
                    history.append(message)
            self.chat_sessions[session_id] = history
            metadata = dict(record.get("metadata") or {})
            metadata.setdefault("created_at", _utc_timestamp())
            metadata.setdefault("updated_at", metadata["created_at"])
            metadata["message_count"] = len(history)
            self.session_metadata[session_id] = metadata

    def _persist_sessions(self) -> None:
        if not self.persistence_enabled:
            return
        payload = {
            "version": 1,
            "sessions": {
                session_id: {
                    "messages": [
                        _serialize_message(message)
                        for message in history
                    ],
                    "metadata": {
                        **self.session_metadata.get(session_id, {}),
                        "message_count": len(history),
                    },
                }
                for session_id, history in self.chat_sessions.items()
            },
        }
        try:
            tmp_path = self.state_file_path.with_suffix(
                self.state_file_path.suffix + ".tmp"
            )
            tmp_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            tmp_path.replace(self.state_file_path)
        except OSError as exc:
            print(f"Failed to persist chat sessions: {exc}", file=sys.stderr)

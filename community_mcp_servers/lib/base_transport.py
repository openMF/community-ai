import os
from typing import Any


__all__ = [
    "StdioTransportMixin",
    "HttpTransportMixin",
]


class StdioTransportMixin:
    def build_stdio_config(
        self,
        command: str,
        args: list[str],
        env_vars: dict[str, str],
    ) -> dict[str, Any]:
        return {
            "transport": "stdio",
            "command": command,
            "args": args,
            "env": env_vars,
        }


class HttpTransportMixin:
    def build_http_config(
        self,
        service_name: str,
        default_url: str,
        transport_type: str = "streamable_http",
    ) -> dict[str, Any]:
        from .utils import build_connection_config
        
        server_url_env = f"{service_name.upper()}_MCP_SERVER_URL"
        api_key_env = f"{service_name.upper()}_MCP_API_KEY"
        
        if not os.getenv(server_url_env):
            raise ValueError(
                f"{server_url_env} is required for {transport_type}"
            )
        
        config = build_connection_config(
            service_name=service_name,
            server_url_env=server_url_env,
            default_server_url=default_url,
            token_env=api_key_env or f"{service_name.upper()}_TOKEN",
            bearer_token_env=api_key_env,
        )
        
        if transport_type == "sse":
            config["transport"] = "sse"
        
        return config

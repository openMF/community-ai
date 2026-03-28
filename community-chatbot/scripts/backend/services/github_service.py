import os
import re
from functools import lru_cache
from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model
from langchain_community.agent_toolkits.github.toolkit import GitHubToolkit
from langchain_community.utilities.github import GitHubAPIWrapper

def sanitize_tool_name(name: str) -> str:
    """Convert tool name to a valid function name."""
    name = name.lower().replace("'", "").replace("'", "")
    name = re.sub(r"[^a-zA-Z0-9_-]+", "_", name) 
    return name.strip("_")

@lru_cache()
def get_github_agent():
    """Initialize the GitHub agent with tools (Singleton)."""
    required_vars = [
        "OPENAI_API_KEY",
        "GITHUB_APP_ID", 
        "GITHUB_REPOSITORY",
        "GITHUB_BRANCH",
        "GITHUB_BASE_BRANCH",
        "GITHUB_APP_PRIVATE_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required env vars for GitHub agent: {', '.join(missing_vars)}")
        
    github = GitHubAPIWrapper()
    toolkit = GitHubToolkit.from_github_api_wrapper(github)
    
    tools = toolkit.get_tools()
    for tool in tools:
        tool.name = sanitize_tool_name(tool.name)
    
    llm = init_chat_model("gpt-4o-mini", model_provider="openai")
    return create_react_agent(llm, tools)

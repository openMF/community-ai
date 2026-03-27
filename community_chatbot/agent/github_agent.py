import os
import getpass
import re
from typing import List
from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model
from langchain_community.agent_toolkits.github.toolkit import GitHubToolkit
from langchain_community.utilities.github import GitHubAPIWrapper

# GitHub Config
if not os.environ.get("GITHUB_REPOSITORY"):
    os.environ["GITHUB_REPOSITORY"] = input("Enter GitHub Repository (e.g., owner/repo): ")

if not os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN"):
    os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"] = getpass.getpass("Enter GitHub Personal Access Token: ")

class PatGitHubAPIWrapper(GitHubAPIWrapper):
    @classmethod
    def validate_environment(cls, values: dict) -> dict:
        from github import Github, Auth
        github_repository = values.get("github_repository") or os.environ.get("GITHUB_REPOSITORY")
        pat = values.get("github_personal_access_token") or os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
        
        # Manually initialize GitHub with PAT
        auth = Auth.Token(pat)
        g = Github(auth=auth)
        repo = g.get_repo(github_repository)
        
        values["github"] = g
        values["github_repo_instance"] = repo
        values["github_repository"] = github_repository
        values["github_base_branch"] = repo.default_branch
        values["active_branch"] = repo.default_branch
        return values


github = PatGitHubAPIWrapper()
toolkit = GitHubToolkit.from_github_api_wrapper(github)
tools = toolkit.get_tools()

def sanitize_tool_name(name: str) -> str:
    """Convert tool name to a valid function name: snake_case with only alphanumerics and _ or -."""
    name = name.lower().replace("'", "").replace("’", "")
    name = re.sub(r"[^a-zA-Z0-9_-]+", "_", name) 
    return name.strip("_")

for tool in tools:
    tool.name = sanitize_tool_name(tool.name)

if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")

llm = init_chat_model("gpt-4o-mini", model_provider="openai")
agent_executor = create_react_agent(llm, tools)

SUMMARY_TRIGGER = 15      
KEEP_LAST = 6             
summary_memory = ""   

def update_summary(old_summary: str, messages: List) -> str:
    """Update conversation summary"""
    prompt = [
        ("system", "You are a summarization assistant. Maintain a concise memory of the conversation."),
        ("user", f"Current summary:\n {old_summary} \n New messages:\n{messages}")
    ]
    response = llm.invoke(prompt)
    return response.content

def build_messages(summary: str, recent_messages: List) -> List:
    """Construct final message list for agent with summary as context"""
    messages = []
    messages.append(("system", "You are a helpful assistant assisting with the repository. DO NOT use tools like create_branch or set_active_branch unless the user explicitly asks you to make changes. If they are just greeting you or chatting, just respond in friendly text without using tools."))
    
    if summary:
        messages.append(("system", f"Conversation summary:\n{summary}"))
    messages.extend(recent_messages)
    return messages

print("GitHub Agent Chatbot (type 'exit' to quit)")
chat_history = []

while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        break

    chat_history.append(("user", user_input))
    
    # Apply summarization if history exceeds threshold
    if len(chat_history) > SUMMARY_TRIGGER:
        print("Summarizing conversation history...")
        summary_memory = update_summary(summary_memory, chat_history[:-KEEP_LAST])
        chat_history = chat_history[-KEEP_LAST:]
    
    messages = build_messages(summary_memory, chat_history)
    
    try:
        events = agent_executor.stream(
            {"messages": chat_history},
            stream_mode="values"
        )
        last_msg=None
        for event in events:
            last_msg = event["messages"][-1]
            last_msg.pretty_print()

        if last_msg:
            chat_history.append(("assistant", last_msg.content))

    except Exception as e:
        print(f"[Error] {e}")

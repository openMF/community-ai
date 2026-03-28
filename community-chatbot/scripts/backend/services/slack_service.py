import os
from langchain_community.agent_toolkits import SlackToolkit
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

def get_slack_agent():
    """Create a new stateful Slack Agent instance."""
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("SLACK_BOT_TOKEN"):
        raise ValueError("Missing OPENAI_API_KEY or SLACK_BOT_TOKEN environment variables")

    llm = ChatOpenAI(model="gpt-4o-mini")
    toolkit = SlackToolkit()
    tools = toolkit.get_tools()
    return create_react_agent(llm, tools)

import os
from functools import lru_cache
from langchain.agents import initialize_agent, AgentType
from langchain_community.utilities.jira import JiraAPIWrapper
from langchain_community.agent_toolkits.jira.toolkit import JiraToolkit
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

class JiraService:
    def __init__(self):
        self.jira_wrapper = None
        self.jira_agent = None
        self.llm = None
        self.jql_generation_prompt = None
        self.summarization_prompt = None
        self._initialize_components()

    def _initialize_components(self):
        print("Initializing Jira and LangChain components...")
        self.jira_wrapper = JiraAPIWrapper()
        toolkit = JiraToolkit.from_jira_api_wrapper(self.jira_wrapper)
        tools = toolkit.get_tools()
        
        self.llm = ChatOpenAI(temperature=0, model="gpt-4-turbo-preview")
        
        agent_kwargs = {
            "prefix": """You are a specialized Jira assistant.
You MUST use the provided tools to answer questions about Jira.
Do NOT answer any questions from your own knowledge.
If a user's query seems like a general knowledge question, you MUST assume it refers to data within Jira.

*** CRITICAL JQL RULE ***
When filtering by a field with a string value that contains spaces (like a person's name, a project name, or a summary), you MUST enclose the value in single or double quotes.
CORRECT: assignee = 'Aru Sharma'
INCORRECT: assignee = Aru Sharma
CORRECT: summary ~ '"New Login Button"'
INCORRECT: summary ~ 'New Login Button'

Always format your response as a Thought, an Action, and an Action Input.
Begin!"""
        }
        
        self.jira_agent = initialize_agent(
            tools,
            self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            agent_kwargs=agent_kwargs,
        )
        
        self.jql_generation_prompt = PromptTemplate.from_template(
            """You are an expert in Jira Query Language (JQL). Your sole task is to convert a user's natural language request into a valid JQL query.
You must only respond with the JQL query string and nothing else.

--- Important JQL Syntax Rules ---
1.  **Quoting:** Any string value containing spaces or special characters MUST be enclosed in single ('') or double ("") quotes.
    -   Example for a name: `assignee = 'Aru Sharma'`
    -   Example for a search phrase: `summary ~ '"Detailed new feature"'`
2.  **Usernames:** When searching for an assignee, it is best to use their name in quotes.

--- Examples ---
User Request: "find all tickets in the 'PROJ' project"
JQL Query: project = 'PROJ'

User Request: "show me all open bugs in the 'Mobile' project assigned to Aru Sharma"
JQL Query: project = 'Mobile' AND issuetype = 'Bug' AND status = 'Open' AND assignee = 'Aru Sharma'

User Request: "what were the top 5 highest priority issues created last week?"
JQL Query: created >= -7d ORDER BY priority DESC

Now, convert the following user request into a JQL query.

User Request: "{user_query}"
JQL Query:"""
        )
        
        self.summarization_prompt = PromptTemplate.from_template(
            """You are a helpful assistant. The user asked the following question:

"{user_query}"

An AI agent attempted to answer this but failed. As a fallback, we ran a JQL query and got the following raw Jira issue data.
Please analyze this data and provide a clear, concise, and helpful answer to the user's original question. If the data seems irrelevant or empty, state that you couldn't find relevant information.

JSON Data:
{json_data}

Based on the data, answer the user's question.
"""
        )

    def run_agent(self, query: str):
        return self.jira_agent.run(query)

    def intelligent_agent_run(self, query: str):
        try:
            print("--- Attempting main agent execution ---")
            response = self.run_agent(query)
            return {
                "response": response,
                "method_used": "agent",
                "query_used": query,
                "success": True
            }
        except Exception as e:
            print(f"\n--- Agent failed, switching to intelligent fallback mode ---\nError: {e}\n")
            print("Generating JQL from natural language...")
            jql_generation_chain = self.jql_generation_prompt | self.llm
            generated_jql = jql_generation_chain.invoke({"user_query": query}).content
            generated_jql = generated_jql.strip().strip("'\"")
            print(f"Dynamically Generated JQL: '{generated_jql}'")

            print("Executing generated JQL query...")
            try:
                fallback_data = self.jira_wrapper.run(mode="jql", query=generated_jql)

                if not fallback_data:
                    return {
                        "response": "The generated JQL query ran successfully but returned no issues. Please try rephrasing your request or be more specific.",
                        "method_used": "fallback",
                        "query_used": generated_jql,
                        "success": True
                    }

                print("Summarizing JQL results for the user...")
                summarization_chain = self.summarization_prompt | self.llm
                final_response = summarization_chain.invoke({
                    "user_query": query,
                    "json_data": fallback_data 
                }).content
                
                return {
                    "response": final_response,
                    "method_used": "fallback",
                    "query_used": generated_jql,
                    "success": True
                }
            except Exception as fallback_e:
                print(f"Fallback JQL execution also failed: {fallback_e}")
                return {
                    "response": f"I'm sorry, I couldn't process your request. Both the primary agent and the fallback query failed. The last error was: {fallback_e}",
                    "method_used": "failed",
                    "query_used": query,
                    "success": False
                }

    def direct_jql_query(self, query: str):
        return self.jira_wrapper.run(mode="jql", query=query)

    def generate_jql(self, natural_query: str) -> str:
        jql_generation_chain = self.jql_generation_prompt | self.llm
        generated_jql = jql_generation_chain.invoke({"user_query": natural_query}).content
        return generated_jql.strip().strip("'\"")

@lru_cache()
def get_jira_service() -> JiraService:
    return JiraService()

from fastmcp import FastMCP
import os
from dotenv import load_dotenv
from atlassian import Jira
from github import Github

# Initialize FastMCP Server
mcp = FastMCP("Mifos Knowledge Librarian")

# Load credentials
load_dotenv()

# Initialize clients
jira_client = Jira(
    url=os.environ["JIRA_INSTANCE_URL"],
    username=os.environ["JIRA_USERNAME"],
    password=os.environ["JIRA_API_TOKEN"]
)
github_client = Github(os.environ["GITHUB_TOKEN"])

@mcp.tool()
def search_jira_tickets(query: str):
    """
    Search for Jira tickets using JQL.
    Used for tracking feature progress and identifying developer consensus.
    """
    try:
        issues = jira_client.jql(query, limit=5)
        results = []
        for issue_data in issues['issues']:
            # The jql result gives us the key and summary, let's get comments
            comments_data = jira_client.get_issue_comments(issue_data['key'])
            comments = [
                f"{c['author']['displayName']}: {c['body']}"
                for c in comments_data['comments'][-3:]
            ]
            results.append({
                "key": issue_data['key'],
                "summary": issue_data['fields']['summary'],
                "comments": comments,
            })
        return results
    except Exception as e:
        return f"Error searching Jira: {e}"

@mcp.tool()
def get_github_pr_details(pr_number: int, repo_name: str):
    """
    Fetch description and changed files from a specific GitHub Pull Request.
    Used for synthesizing release notes.
    """
    try:
        repo = github_client.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        files = [f.filename for f in pr.get_files()]
        return {
            "title": pr.title,
            "description": pr.body,
            "changed_files": files,
        }
    except Exception as e:
        return f"Error fetching GitHub PR: {e}"

@mcp.tool()
def generate_knowledge_summary(jira_key: str, repo_name: str = "apache/fineract"):
    """
    Takes a Jira Key, searches for a corresponding GitHub PR in a specified repo,
    and returns a combined summary of the ticket and the PR.
    Defaults to the 'apache/fineract' repository.
    """
    try:
        # 1. Get Jira ticket info
        jira_info_list = search_jira_tickets(f'key = {jira_key}')
        if not jira_info_list or isinstance(jira_info_list, str):
            return f"Could not retrieve Jira ticket {jira_key}."
        jira_info = jira_info_list[0]

        # 2. Find corresponding GitHub PR
        query = f'repo:{repo_name} is:pr "{jira_key}"'
        prs = github_client.search_issues(query)
        if prs.totalCount == 0:
            return {
                "jira_summary": jira_info['summary'],
                "jira_comments": jira_info['comments'],
                "github_pr": "No corresponding GitHub PR found."
            }

        # 3. Get PR details from the first match
        pr_number = prs[0].number
        pr_details = get_github_pr_details(pr_number, repo_name)

        # 4. Combine and return
        return {
            "jira_key": jira_key,
            "jira_summary": jira_info['summary'],
            "jira_comments": jira_info['comments'],
            "github_pr_title": pr_details.get('title'),
            "github_pr_description": pr_details.get('description'),
            "github_pr_changed_files": pr_details.get('changed_files'),
        }
    except Exception as e:
        return f"Error generating knowledge summary: {e}"

@mcp.tool()
def search_project_docs(query: str):
    """
    Search through static Mifos documentation and READMEs.
    Use this for architectural questions or project setup guides.
    """
    # Simple implementation: search for keywords in .md files
    docs_path = "./docs" # Or root if docs/ doesn't exist
    results = []
    if not os.path.exists(docs_path):
        docs_path = "." # Fallback to root
        
    for root, dirs, files in os.walk(docs_path):
        for file in files:
            if file.endswith(".md"):
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    content = f.read()
                    if query.lower() in content.lower():
                        results.append(f"--- {file} ---\n{content[:500]}...")
    
    return "\n".join(results) if results else "No matching documentation found."

if __name__ == "__main__":
    mcp.run()
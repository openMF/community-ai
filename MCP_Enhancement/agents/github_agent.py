import logging
from typing import Optional, List
from github import Github
from github.GithubException import GithubException


from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

# Robust import to handle running from different directories
try:
    from MCP_Enhancement.src.core.config import get_settings
except ImportError:
    from MCP_Enhancement.config import get_settings

logger = logging.getLogger(__name__)

# --- Reusable Prompts ---

GITHUB_SUMMARY_PROMPT = PromptTemplate.from_template(
    """The user is asking about activity in the GitHub repository: "{repo_name}".

I have retrieved the following live data from GitHub:
{raw_data}

User Question: "{user_query}"

Provide a professional, clear summary.
- Highlight any "failing" CI statuses or "blocked" PRs.
- Mention specific authors.
"""
)


# --- Helper Logic ---

def get_github_client() -> Github:
    """
    Initializes the PyGithub client using credentials from .env
    """
    settings = get_settings()
    # Uses the GITHUB_TOKEN (PAT) for authentication
    return Github(settings.GITHUB_TOKEN.get_secret_value())


def get_repo(client: Github):
    """Helper to get the specific repository object"""
    settings = get_settings()
    return client.get_repo(settings.GITHUB_REPOSITORY)


def get_llm():
    settings = get_settings()
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY.get_secret_value(),
        temperature=0
    )


# --- Primary Tools for MCP ---

def get_repo_overview(query: str) -> str:
    """
    General search tool. Fetches the 5 most recent open PRs and Issues.
    """
    client = get_github_client()
    try:
        repo = get_repo(client)

        # Fetch raw objects (limit to 5 to save context)
        prs = repo.get_pulls(state='open', sort='updated', direction='desc')[:5]
        issues = repo.get_issues(state='open', sort='updated', direction='desc')[:5]

        # Format for the LLM
        pr_text = "\n".join([f"- PR #{p.number}: {p.title} (by {p.user.login}) - Status: {p.state}" for p in prs])
        issue_text = "\n".join([f"- Issue #{i.number}: {i.title} (by {i.user.login})" for i in issues])

        raw_data = f"Recent Open Pull Requests:\n{pr_text}\n\nRecent Open Issues:\n{issue_text}"

        # Summarize
        llm = get_llm()
        summary_chain = GITHUB_SUMMARY_PROMPT | llm
        return summary_chain.invoke({
            "repo_name": repo.full_name,
            "raw_data": raw_data,
            "user_query": query
        }).content

    except Exception as e:
        logger.error(f"GitHub Overview failed: {e}")
        return f"Error accessing GitHub: {str(e)}"


def get_pr_details(pr_number: int) -> str:
    """
    Fetches deep context for a specific PR, including specific files changed.
    """
    client = get_github_client()
    try:
        repo = get_repo(client)
        pr = repo.get_pull(pr_number)

        # Get list of files changed
        files = [f.filename for f in pr.get_files()][:10]
        file_list = ", ".join(files)

        return (
            f"PR #{pr.number}: {pr.title}\n"
            f"State: {pr.state}\n"
            f"Author: {pr.user.login}\n"
            f"Body: {pr.body}\n"
            f"Files Changed: {file_list}"
        )
    except Exception as e:
        return f"Could not find PR #{pr_number}: {str(e)}"


def check_ci_status(pr_number: Optional[int] = None) -> str:
    """
    Checks the CI/Build status.
    If pr_number is provided, checks that PR.
    Otherwise, checks the main branch.
    """
    client = get_github_client()
    try:
        repo = get_repo(client)

        if pr_number:
            # Check specific PR
            pr = repo.get_pull(pr_number)
            # Get the commit SHA of the head (the latest code in the PR)
            sha = pr.head.sha
            context_label = f"PR #{pr_number}"
        else:
            # Check default branch (usually 'develop' or 'master')
            branch = repo.get_branch(repo.default_branch)
            sha = branch.commit.sha
            context_label = f"Branch '{repo.default_branch}'"

        # Fetch status
        commit = repo.get_commit(sha)
        # combined_status returns the aggregate (success, failure, pending)
        status = commit.get_combined_status()

        return f"CI Status for {context_label}: {status.state.upper()} (SHA: {sha[:7]})"

    except Exception as e:
        logger.error(f"CI Check failed: {e}")
        return f"Error checking CI status: {str(e)}"


def create_pull_request(title: str, body: str, head_branch: str, base_branch: str = "develop") -> str:
    """
    Creates a new PR.
    """
    client = get_github_client()
    try:
        repo = get_repo(client)
        pr = repo.create_pull(
            title=title,
            body=body,
            head=head_branch,
            base=base_branch
        )
        return f"Successfully created PR #{pr.number}: {pr.html_url}"
    except GithubException as e:
        return f"Failed to create PR: {e.data.get('message', str(e))}"
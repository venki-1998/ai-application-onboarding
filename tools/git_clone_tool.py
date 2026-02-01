from langchain.tools import tool
from helpers.git_helper import clone_repository

@tool("clone_repository_tool")
def clone_repository_tool(git_url: str, app_type: str) -> str:
    """
    Tool: Clones a Git repository for the given app type.
    Args:
        git_url: Git URL of the repository.
        app_type: Application type (NodeJS, Python, Java, etc.)
    """
    path = clone_repository(git_url)
    return f"Repository cloned successfully for {app_type} app.\nLocal path: {path}"

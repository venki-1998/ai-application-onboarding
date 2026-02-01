# agents/git_pr_agent.py
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from helpers.git_pr_helper import create_pull_request

import logging
logger = logging.getLogger(__name__)


# Simple agent (tool wrapper could be added if needed)
def run_git_pr_agent(workspace_path: str, git_remote: str):
    try:
        result = create_pull_request(workspace_path, git_remote)
        if isinstance(result, dict):
            return result
        return {"success": True, "message": str(result)}
    except Exception as e:
        return {"success": False, "error": str(e)}

from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from tools.git_clone_tool import clone_repository_tool

# Initialize Groq LLM (ensure your GROQ_API_KEY is set)
from helpers.config_loader import get_llm
llm = get_llm()

system_prompt = """
You are an AI DevOps assistant.
When the user asks to clone a repository, call the clone_repository_tool.
Ensure you are running only ONCE and return the response quick
"""

# Create the agent
git_clone_agent = create_agent(
    model=llm,
    tools=[clone_repository_tool],
    system_prompt=system_prompt,
)

# Prevent recursion
git_clone_agent.config = {"recursion_limit": 5, "stop_on_first_tool": True, }

import re

def _extract_tool_output(result):
    """
    Extracts clean text content from all ToolMessage objects in an agent response,
    and also tries to detect a workspace path if mentioned in the content.

    Returns:
        List[dict]: Each dict contains:
            - 'content': str, the tool output
            - 'workspace_path': str or None, extracted from content if found
    """
    messages = result.get("messages", [])
    outputs = []

    for msg in messages:
        # Detect ToolMessage by type or class name
        if getattr(msg, "type", None) == "tool" or "ToolMessage" in str(type(msg)):
            content = getattr(msg, "content", None)
            if content:
                # Try to extract workspace path from content
                match = re.search(r"Local path:\s*(\S+)", content)
                workspace_path = match.group(1) if match else None

                outputs.append({
                    "content": content,
                    "workspace_path": workspace_path
                })

    if not outputs:
        outputs.append({"content": "No ToolMessage content found.", "workspace_path": None})
    
    return outputs


def run_git_clone_agent(git_url: str, app_type: str):
    """
    Executes the agent to perform Git clone operation.
    """
    query = f"Clone the repository from {git_url} for a {app_type} application."
    result = git_clone_agent.invoke({"messages": [HumanMessage(content=query)]})
    return _extract_tool_output(result)

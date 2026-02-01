from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from tools.dockerfile_tool import fetch_or_generate_dockerfile
from helpers.config_loader import get_llm

llm = get_llm()

SYSTEM_PROMPT = """
You are an AI DevOps assistant.
Search for the exact app_type value defined and then fetch teh data from qdrant first 
Ensure you are calling fetch_or_generate_dockerfile tool when invoked
When asked to generate a Dockerfile, you should fetch from Qdrant if it exists,
otherwise generate a Dockerfile using LLM and save it to the workspace.
Ensure you are running ONLY ONCE 
"""

DOCKERFILE_AGENT = create_agent(
    model=llm,
    tools=[fetch_or_generate_dockerfile],
    system_prompt=SYSTEM_PROMPT
)

DOCKERFILE_AGENT.config = {
    "recursion_limit": 10,
    "stop_on_first_tool": True,  # <--- new flag to prevent re-invoking
    # "return_intermediate_steps": False
}

def run_dockerfile_agent(app_type: str, workspace_path: str):
    query = f"Generate a Dockerfile for {app_type} application in the workspace {workspace_path}."
    print(f"workspace_path passed: {workspace_path}")
    result = DOCKERFILE_AGENT.invoke({"messages": [HumanMessage(content=query)]})
    # Extract only ToolMessage content (clean output)
    for msg in result.get("messages", []):
        if "ToolMessage" in str(type(msg)):
            return msg.content
    return "Dockerfile generation failed."

import json
from langchain.agents import create_agent
from tools.build_publish_tool import build_push_tool
from langchain_core.messages import HumanMessage

from helpers.config_loader import get_llm

llm = get_llm()

TOOLS_BUILD_PUSH = [build_push_tool]

SYSTEM_PROMPT_BUILD_PUSH = """
You are BuildPushAgent.
You must call the tool `build_push_tool` exactly **once**.
Instructions:
1. You will receive structured input with fields:
   { "app_type": "<type>", "image_name_tag": "<tag>", "workspace_path": "<path>", "raw_dockerfile": "<optional>" }
2. Immediately call `build_push_tool` with this input as a JSON string.
3. When the tool returns, **do not call any tools again**.
   Do not reflect, reason, or retry.
   Simply return the tool output **verbatim** as your final answer.
4. The output must always be valid JSON.
   Never wrap it in text or Markdown. Never say anything else.
If you have already called `build_push_tool` and received its result, STOP.
Return it as-is and end the run.
"""

# Create the agent
build_push_agent = create_agent(
    model=llm,
    tools=TOOLS_BUILD_PUSH,
    system_prompt=SYSTEM_PROMPT_BUILD_PUSH
)

# Prevent recursion
build_push_agent.config = {"recursion_limit": 10}


def run_build_push_agent(app_type: str, image_name_tag: str, workspace_path: str, raw_dockerfile: str = None):
    """
    Run the build & push agent once safely.
    """
    payload = {
        "app_type": app_type,
        "image_name_tag": image_name_tag,
        "workspace_path": workspace_path,
        "raw_dockerfile": raw_dockerfile
    }

    result = build_push_agent.invoke({"messages": [HumanMessage(content=json.dumps(payload))]})
    # Extract the content safely
    if isinstance(result, HumanMessage):
        output = result.content
    elif isinstance(result, dict) and "output" in result:
        # Some agent returns structured dict
        output = result["output"]
    elif isinstance(result, list) and len(result) > 0 and hasattr(result[0], "content"):
        output = result[0].content
    else:
        output = str(result)

    # Print for debugging
    print("🟢 Agent Result:", output)
    
    return output
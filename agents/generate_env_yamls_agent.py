import json
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from tools.generate_env_yamls_tool import generate_env_yamls_tool

from helpers.config_loader import get_llm

llm = get_llm()

import logging
logger = logging.getLogger(__name__)

# Use your existing LLM variable `llm` (do not replace). If you prefer a helper get_llm(), swap accordingly.
SYSTEM_PROMPT = """
You are a Kubernetes YAML generation agent.
You will receive a JSON payload describing {app_type}, {app_name}, {envs}, {workspace_path}, {image_tag}.
Call the tool `generate_env_yamls_tool` exactly once with that JSON string, then return the tool output verbatim (pure JSON). Do not call any other tools or emit extra text.
"""

AGENT_TOOLS = [generate_env_yamls_tool]

generate_env_yamls_agent = create_agent(
    model=llm,
    tools=AGENT_TOOLS,
    system_prompt=SYSTEM_PROMPT
)

# Prevent recursion if supported
try:
    generate_env_yamls_agent.config = {"recursion_limit": 10, "stop_on_first_tool": True}
except Exception:
    pass


def run_generate_env_yamls_agent(app_type: str, app_name: str, envs: list, workspace_path: str, image_tag: str = None):
    payload = {
        "app_type": app_type,
        "app_name": app_name,
        "envs": envs,
        "workspace_path": workspace_path,
        "image_tag": image_tag
    }
    print(f"sending payload to tool - generate_env_yamls_tool- {payload}")
    result = generate_env_yamls_agent.invoke({"messages":[HumanMessage(content=json.dumps(payload))]})

    # Extract tool output safely (tool returns JSON string)
    if isinstance(result, dict) and "messages" in result:
        for m in result.get("messages", []):
            if getattr(m, "type", "") == "tool" or "ToolMessage" in str(type(m)):
                return getattr(m, "content", str(result))
        return str(result)
    # if string or HumanMessage-like, coerce to str
    return str(result)

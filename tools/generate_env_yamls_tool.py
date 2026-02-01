import os
import json
from langchain.tools import tool
from helpers.k8s_env_generator import generate_env_yamls

@tool
def generate_env_yamls_tool(input_text: str) -> str:
    """
    Expects JSON string:
    {
      "app_type": "python",
      "app_name": "myapp",
      "envs": ["dev","uat"],
      "image_tag": "shan5a6/myapp:v1.0.0",
      "workspace_path": "/tmp/workspace-x123"   # REQUIRED: target workspace
    }
    Returns JSON:
    { "status":"success", "generated": {"dev": ["/tmp/..."], ...} }
    """
    print("Inside tool generate_env_yamls_tool")
    print(input_text)
    
    try:
        data = json.loads(input_text)
    except Exception:
        return json.dumps({"status":"failed","error":"invalid JSON input"})

    app_type = data.get("app_type")
    app_name = data.get("app_name")
    envs = data.get("envs", [])
    workspace_path = data.get("workspace_path")
    image_tag = data.get("image_tag")

    if not app_type or not app_name or not envs or not workspace_path:
        return json.dumps({"status":"failed","error":"missing required fields (app_type, app_name, envs, workspace_path, image_tag)"})

    if not os.path.exists(workspace_path):
        return json.dumps({"status":"failed","error":f"workspace_path not found: {workspace_path}"})

    try:
        generated = generate_env_yamls(app_type, app_name, envs, workspace_path, image_tag=image_tag)
        return json.dumps({"status":"success", "generated": generated})
    except Exception as e:
        return json.dumps({"status":"failed", "error": str(e)})

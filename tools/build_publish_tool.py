import os
import json
import subprocess
from langchain_core.tools import tool

@tool
def build_push_tool(input_text: str) -> str:
    """
    Build and push a Docker image to a registry.
    Expects JSON input like:
    {
      "app_type": "Java",
      "image_name_tag": "shan5a6/myappimage:v1.0.0",
      "workspace_path": "/tmp/onboard-xyz",
      "raw_dockerfile": "<optional dockerfile text>"
    }
    """
    try:
        try:
            data = json.loads(input_text)
        except json.JSONDecodeError:
            data = {"workspace_path": "/tmp/onboard", "image_name_tag": "unknown", "app_type": "Unknown"}

        workspace_path = data.get("workspace_path")
        image_name_tag = data.get("image_name_tag")
        dockerfile_text = data.get("raw_dockerfile")

        if not os.path.exists(workspace_path):
            return json.dumps({"status": "failed", "error": f"Workspace not found: {workspace_path}"})

        dockerfile_path = os.path.join(workspace_path, "Dockerfile")

        # If Dockerfile text is provided
        if dockerfile_text:
            with open(dockerfile_path, "w") as f:
                f.write(dockerfile_text.strip())
            print(f"✅ Dockerfile written to {dockerfile_path}")
        elif not os.path.exists(dockerfile_path):
            return json.dumps({"status": "failed", "error": "No Dockerfile found or provided."})

        # Docker build
        build_cmd = ["docker", "build", "-t", image_name_tag, workspace_path]
        print(f"🏗️  Building Docker image: {' '.join(build_cmd)}")
        build_process = subprocess.run(build_cmd, capture_output=True, text=True)
        if build_process.returncode != 0:
            return json.dumps({"status": "failed", "step": "build", "stderr": build_process.stderr})

        print(f"✅ Build complete: {image_name_tag}")

        # Docker push
        push_cmd = ["docker", "push", image_name_tag]
        print(f"📤 Pushing image: {' '.join(push_cmd)}")
        push_process = subprocess.run(push_cmd, capture_output=True, text=True)
        if push_process.returncode != 0:
            return json.dumps({"status": "failed", "step": "push", "stderr": push_process.stderr})

        result = {
            "status": "success",
            "image": image_name_tag,
            "workspace": workspace_path,
            "message": f"Docker image {image_name_tag} successfully built and pushed."
        }
        print(json.dumps(result))
        return json.dumps(result)

    except Exception as e:
        return json.dumps({"status": "failed", "error": str(e)})

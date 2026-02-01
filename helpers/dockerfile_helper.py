import os

def save_dockerfile(workspace_path: str, content: str, filename="Dockerfile"):
    """
    Saves the Dockerfile content to the specified workspace.
    """
    
    if not os.path.exists(workspace_path):
        os.makedirs(workspace_path)
    file_path = os.path.join(workspace_path, filename)
    with open(file_path, "w") as f:
        f.write(content)
    print(f"file path is {file_path}")
    return file_path

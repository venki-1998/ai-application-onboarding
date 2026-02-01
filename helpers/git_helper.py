import os
import subprocess
import tempfile
import random
import string

import logging
from git import Repo, GitCommandError

logger = logging.getLogger(__name__)


def generate_random_workspace_name(prefix="workspace-x", length=4):
    """Generate a short random workspace name like workspace-x1234."""
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"{prefix}{suffix}"

def clone_repository(git_url: str) -> str:
    """
    Clone a git repository into a temporary random workspace directory.
    Returns the local path of the cloned repository.
    """
    try:
        workspace_name = generate_random_workspace_name()
        base_dir = tempfile.gettempdir()
        workspace_path = os.path.join(base_dir, workspace_name)

        subprocess.run(["git", "clone", git_url, workspace_path], check=True)
        return workspace_path

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Git clone failed: {e}")
    except Exception as ex:
        raise RuntimeError(f"Unexpected error while cloning: {ex}")



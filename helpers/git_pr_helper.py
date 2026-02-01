import os
import subprocess
from github import Github
from git import Repo
from datetime import datetime

def create_pull_request(workspace_path: str, git_remote: str):
    """
    Pushes local changes and creates a GitHub PR.
    """
    git_username = os.getenv("GIT_USERNAME")
    git_token = os.getenv("GIT_TOKEN")

    if not git_username or not git_token or not git_remote:
        raise ValueError("GIT_USERNAME, GIT_TOKEN, and git_remote must be provided.")

    branch_name = f"ai-onboard-changes-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    commit_message = f"AI Onboarding changes - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    repo = Repo(workspace_path)

    # Ensure clean branch creation
    if branch_name in [h.name for h in repo.heads]:
        repo.git.checkout(branch_name)
    else:
        repo.git.checkout('HEAD', b=branch_name)

    # Stage and commit changes if any
    repo.git.add(A=True)
    try:
        diff = repo.git.diff('--cached')
        if not diff.strip():
            print("⚠️ No new diff found, committing anyway (forced).")
        repo.index.commit(commit_message)
    except Exception:
        repo.index.commit(commit_message)

    # Push to remote
    remote_url = git_remote.replace(
        "https://",
        f"https://{git_username}:{git_token}@"
    )

    origin = repo.create_remote('auth-origin', remote_url) if 'auth-origin' not in [r.name for r in repo.remotes] else repo.remote('auth-origin')
    origin.push(branch_name, force=True)

    # Create PR via GitHub API
    g = Github(git_token)
    owner_repo = git_remote.replace("https://github.com/", "").replace(".git", "")
    gh_repo = g.get_repo(owner_repo)
    pr = gh_repo.create_pull(
        title="AI Onboarding Automated Pull Request",
        body="This PR was automatically created by AI DevOps Onboarder.",
        head=branch_name,
        base="master"
    )

    return {
        "success": True,
        "message": f"✅ Pull request created successfully: {pr.html_url}"
    }

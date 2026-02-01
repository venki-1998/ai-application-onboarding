import streamlit as st
from agents.git_clone_agent import run_git_clone_agent
from agents.dockerfile_agent import run_dockerfile_agent
from agents.build_publish_agent import run_build_push_agent
from agents.generate_env_yamls_agent import run_generate_env_yamls_agent
from agents.git_pr_agent import run_git_pr_agent

import os
import json
from dotenv import load_dotenv
# Load environment variables from .env
load_dotenv()

st.set_page_config(page_title="AI Application Onboarding", page_icon="🚀", layout="centered")

st.title("🤖 AI Application Onboarding Platform")
st.markdown("Seamlessly onboard your applications into Kubernetes!")

# -------------------------------
# Step 1: Get Inputs
# -------------------------------
st.header("1️⃣ Repository Details")

git_url = st.text_input("🔗 Enter your Git Repository URL", placeholder="https://github.com/org/sample-app.git")
app_type = st.selectbox("⚙️ Select Application Type", ["Select Type", "NodeJS", "Python", "Java", ".NET"], index=0)
st.session_state.app_type = app_type
st.session_state.git_url = git_url
# -------------------------------
# Step 2: Clone Button
# -------------------------------
if st.button("📦 Clone Repository"):
    if not git_url or app_type == "Select Type":
        st.warning("⚠️ Please provide both Git URL and Application Type.")
    else:
        with st.spinner("🧠 Cloning repository... please wait..."):
            try:
                result = run_git_clone_agent(git_url, app_type)
                st.success("✅ Clone Completed Successfully!")
                for output in result:
                    st.text_area("Agent Output", value=output, height=150)
                    # Extract workspace path
                    workspace_path = output.get('workspace_path', None)
                    st.session_state.workspace_path = workspace_path
            except Exception as e:
                st.error(f"❌ Clone Failed: {e}")


st.header("2️⃣ Dockerfile Generation")

if st.button("🛠️ Generate Dockerfile"):
    if not git_url or app_type == "Select Type":
        st.warning("⚠️ Please provide Git URL and Application Type first.")
    else:
        with st.spinner("Generating Dockerfile..."):
            try:
                workspace_path = st.session_state.get("workspace_path", None)
                st.code(workspace_path, language="dockerfile")
                dockerfile_path = run_dockerfile_agent(app_type, workspace_path)  # workspace_path from clone step
                st.success(f"✅ Dockerfile saved at: {dockerfile_path}")
                st.code(open(dockerfile_path).read(), language="dockerfile")
            except Exception as e:
                st.error(f"❌ Dockerfile generation failed: {e}")

# ===========================================
# Step 3: Build & Publish Image
# ===========================================
st.header("3 Build & Publish Docker Image")

registry_input = st.text_input("🏷️ Enter Image Tag (e.g., shan5a6/myapp:v1.0.0)")
workspace_path = st.session_state.get("workspace_path", None)
st.session_state.image_tag = registry_input
if st.button("🚀 Build & Publish Image"):
    if not registry_input or not workspace_path:
        st.warning("⚠️ Please provide Image Tag and ensure the repo is cloned.")
    else:
        with st.spinner("Building and pushing Docker image..."):
            try:
                result = run_build_push_agent(app_type, registry_input, workspace_path)
                st.success("✅ Build & Publish Completed!")
            except Exception as e:
                st.error(f"❌ Build & Publish Failed: {e}")

# ===========================================
# Step 4: Generate YAML Files
# ===========================================

st.markdown('<div class="card">', unsafe_allow_html=True)
st.header("Generate environment-specific Kubernetes YAMLs")

app_name = st.text_input("Application Name", placeholder="myapp")
app_type = st.session_state.get("app_type")
envs = st.multiselect("Select environments", ["dev", "sit", "uat", "pt", "preprod", "prod"], default=["dev"])
workspace_path = st.session_state.get("workspace_path", None)
image_tag = st.session_state.image_tag

if st.button("Generate YAMLs for environments"):
    if not app_name or not envs:
        st.warning("Provide application name and select environments.")
    else:
        if not os.path.exists(workspace_path):
            st.error(f"Workspace path not found: {workspace_path}")
        else:
            with st.spinner("Generating YAMLs..."):
                try:
                    print("Calling run_generate_env_yamls_agent")
                    result = run_generate_env_yamls_agent(app_type, app_name, envs, workspace_path, image_tag=image_tag )
                    # result is JSON string
                    try:
                        j = json.loads(result)
                    except Exception:
                        st.error("Agent returned non-JSON output.")
                        st.text_area("Raw output", value=str(result), height=300)
                        st.markdown('</div>', unsafe_allow_html=True)
                        raise st.stop()

                    if j.get("status") == "success":
                        st.success("YAMLs generated successfully.")
                        generated = j.get("generated", {})
                        for env, files in generated.items():
                            st.subheader(f"{env} — {len(files)} files")
                            for f in files:
                                st.markdown(f"**{os.path.basename(f)}** — `{f}`")
                                try:
                                    st.code(open(f, "r", encoding="utf-8").read(), language="yaml")
                                except Exception as e:
                                    st.text(f"Could not read file: {e}")
                        st.session_state.k8s_generated = generated
                    else:
                        st.error(f"Generation failed: {j.get('error')}")
                        st.text_area("Tool output", value=json.dumps(j, indent=2), height=300)
                except Exception as e:
                    st.error(f"Error: {e}")

st.markdown('</div>', unsafe_allow_html=True)
# ===========================================
# Step 5: Raise a Pull Request
# ===========================================

st.header("🚀 AI Onboarding: Create Git Pull Request")

workspace_path = st.session_state.get("workspace_path")
git_remote = st.session_state.get("git_url")  # dynamically from UI session
print(f"provide giturl is {git_remote}")

if st.button("Create Pull Request"):
    if not workspace_path or not git_remote:
        st.warning("⚠️ Workspace path or Git URL not set.")
    else:
        with st.spinner("Creating pull request..."):
            result = run_git_pr_agent(workspace_path, git_remote)
            if result.get("success"):
                st.success(result.get("message"))
            else:
                st.error(result.get("message") or result.get("error") or "❌ Unknown failure.")

st.markdown("---")
st.caption("© 2025 AI DevOps Onboarding | Powered by LangChain + Streamlit")

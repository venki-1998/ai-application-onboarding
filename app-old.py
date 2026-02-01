import streamlit as st
from agents.git_clone_agent import run_git_clone_agent
from agents.dockerfile_agent import run_dockerfile_agent

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

st.markdown("---")
st.caption("© 2025 AI DevOps Onboarding | Powered by LangChain + Streamlit")

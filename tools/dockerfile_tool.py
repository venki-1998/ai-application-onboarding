from helpers.qdrant_helper import client
from helpers.dockerfile_helper import save_dockerfile
from sentence_transformers import SentenceTransformer
from langchain.tools import tool
import os
from langchain_groq import ChatGroq

llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))
embedder = SentenceTransformer("all-MiniLM-L6-v2")

@tool("fetch_or_generate_dockerfile")
def fetch_or_generate_dockerfile(app_type: str, workspace_path: str) -> str:
    """
    Fetch or generate Dockerfile template based on app_type.
    """
    collection_name = "dockerfiles"
    print(f"🧩 fetch_or_generate_dockerfile: workspace={workspace_path}, app_type={app_type}")

    # Embed the app_type to do a vector-based semantic search
    query_vector = embedder.encode(app_type).tolist()

    # Search the most similar Dockerfile
    search_results = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        query_filter={"must": [{"key": "app_type", "match": {"value": app_type.lower()}}]},
        limit=1
    )

    if search_results:
        content = search_results[0].payload.get("file_content", "")
        print(f"✅ Retrieved Dockerfile from Qdrant for '{app_type}'")
    else:
        print(f"⚠️ No Dockerfile found for '{app_type}', generating via LLM...")
        prompt = f"Generate a production-ready Dockerfile for a {app_type} app deployable in Kubernetes."
        response = llm.chat([{"role": "user", "content": prompt}])
        content = response.content if hasattr(response, "content") else str(response)

    file_path = save_dockerfile(workspace_path, content)
    print(f"📄 Dockerfile saved to {file_path}")
    return file_path

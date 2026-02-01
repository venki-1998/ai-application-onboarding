from qdrant_client import QdrantClient, models

# Connect to local Qdrant (adjust URL if remote)
client = QdrantClient(host="localhost", port=6333)

collection_name = "dockerfiles"

# --- Option 1: Retrieve all stored Dockerfiles ---
def list_all_dockerfiles():
    try:
        response = client.scroll(
            collection_name=collection_name,
            limit=10,  # Adjust if you have more
            with_payload=True,
            with_vectors=False
        )

        points, next_page = response
        if not points:
            print("⚠️ No Dockerfiles found in Qdrant.")
            return

        for point in points:
            app_type = point.payload.get("app_type", "unknown")
            print(f"\n🔹 App Type: {app_type}")
            print(f"📄 Path: {point.payload.get('file_path')}")
            print(f"🧠 Vector size: {len(point.vector) if point.vector else 'N/A'}")
            print("🧾 Content Preview:")
            print(point.payload.get("file_content", "")[:400])
            print("-" * 80)

    except Exception as e:
        print(f"❌ Error while fetching data: {e}")


# --- Option 2: Retrieve specific app_type ---
def get_dockerfile_by_app(app_type: str):
    try:
        response = client.scroll(
            collection_name=collection_name,
            limit=1,
            with_payload=True,
            with_vectors=False,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="app_type",
                        match=models.MatchValue(value=app_type.lower())
                    )
                ]
            )
        )

        points, _ = response
        if not points:
            print(f"⚠️ No Dockerfile found for app_type: {app_type}")
            return

        p = points[0]
        print(f"✅ Found Dockerfile for {app_type}")
        print(f"📄 Path: {p.payload.get('file_path')}")
        print("\n🧾 Content:\n" + "-" * 60)
        print(p.payload.get("file_content", ""))

    except Exception as e:
        print(f"❌ Error while fetching {app_type}: {e}")


if __name__ == "__main__":
    print("🧠 Testing Qdrant Dockerfile retrieval...\n")

    # Option 1: list all
    list_all_dockerfiles()

    # Option 2: fetch specific app_type
    # Uncomment below line to test for a specific language:
    # get_dockerfile_by_app("python")

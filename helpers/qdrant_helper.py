import os
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance

import uuid
from sentence_transformers import SentenceTransformer
from qdrant_client.http.models import VectorParams, Distance

# -------------------------------
# Qdrant client setup
# -------------------------------
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# -------------------------------
# Function to create collection
# -------------------------------
def create_dockerfiles_collection(collection_name="dockerfiles", vector_size=768):
    """
    Creates a Qdrant collection for storing Dockerfiles with vector indexing.
    """
    if collection_name not in [c.name for c in client.get_collections().collections]:
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )
        print(f"✅ Collection '{collection_name}' created with vector size {vector_size}.")
    else:
        print(f"ℹ️ Collection '{collection_name}' already exists.")

# -------------------------------
# Function to inject dockerfiles
# -------------------------------

from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
import os
import hashlib

client = QdrantClient("localhost", port=6333)
model = SentenceTransformer("all-MiniLM-L6-v2")
collection_name = "dockerfiles"

import uuid
import hashlib

def deterministic_id(app_type: str) -> str:
    """Generate a deterministic UUID based on app_type."""
    import uuid, hashlib
    hash_bytes = hashlib.sha256(app_type.encode()).digest()[:16]
    return str(uuid.UUID(bytes=hash_bytes))

def inject_dockerfiles_to_qdrant(base_dir="dockerfiles"):
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
        )
        print(f"✅ Created collection '{collection_name}'")
    else:
        print(f"ℹ️ Collection '{collection_name}' already exists.")

    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.lower() == "dockerfile":
                file_path = os.path.join(root, file)
                app_type = os.path.basename(root).lower()

                with open(file_path, "r") as f:
                    content = f.read()

                vector = model.encode(content).tolist()

                payload = {
                    "file_content": content,
                    "language": app_type,
                    "app_type": app_type,
                    "file_path": file_path
                }

                # 🔥 Remove existing data
                client.delete(
                    collection_name=collection_name,
                    points_selector=models.FilterSelector(
                        filter=models.Filter(
                            must=[models.FieldCondition(
                                key="app_type",
                                match=models.MatchValue(value=app_type)
                            )]
                        )
                    )
                )

                # 🧩 Insert with deterministic UUID
                point_id = deterministic_id(app_type)
                client.upsert(
                    collection_name=collection_name,
                    points=[
                        models.PointStruct(
                            id=point_id,
                            vector=vector,
                            payload=payload,
                        )
                    ],
                )

                print(f"✅ Replaced Dockerfile for app_type: {app_type}")


def fetch_dockerfile(app_type: str, collection_name="dockerfiles"):
    """
    Retrieve Dockerfile content from Qdrant for a given app_type.
    """
    query_filter = {
        "must": [
            {"key": "app_type", "match": {"value": app_type.lower()}}
        ]
    }

    results = client.search(
        collection_name=collection_name,
        query_vector=[0.0]*384,  # dummy vector, using filter only
        query_filter=query_filter,
        limit=1
    )

    if results and len(results) > 0:
        return results[0].payload.get("file_content", None)
    return None



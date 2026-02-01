import os
import json
import hashlib
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import VectorParams, Distance
from sentence_transformers import SentenceTransformer

# config from env (fallbacks)
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = os.getenv("K8S_QDRANT_COLLECTION", "kubernetes_configs")
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
VECTOR_SIZE = int(os.getenv("EMBED_DIM", 384))

# Initialize
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
embedder = SentenceTransformer(EMBED_MODEL_NAME)


# -------------------------
# Helpers
# -------------------------
def _deterministic_uuid_for_path(path: str) -> str:
    """
    Create a deterministic UUID from a file path so repeated injections replace existing point.
    """
    h = hashlib.sha256(path.encode("utf-8")).digest()[:16]
    return str(uuid.UUID(bytes=h))


def ensure_collection(collection_name: str = COLLECTION_NAME, vector_size: int = VECTOR_SIZE):
    """
    Create/recreate collection if not exists with the right vector size.
    """
    existing = [c.name for c in client.get_collections().collections]
    if collection_name not in existing:
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE)
        )
        print(f"✅ Created collection '{collection_name}' (vector_size={vector_size})")
    else:
        # optionally check vector size consistency — skip here
        print(f"ℹ️ Collection '{collection_name}' already exists.")


# -------------------------
# Injection function
# -------------------------
def inject_k8s_templates(
    base_dir: str = "k8s-templates",
    collection_name: str = COLLECTION_NAME,
    embed: bool = True,
):
    """
    Walk base_dir and ingest YAML/text files into Qdrant.
    Directory layout expected:
        k8s-templates/
          ├─ java/
          │   ├─ configmaps/configmap.yaml
          │   ├─ deployments/deploy.yaml
          │   └─ service/svc.yaml
          ...
    Each file becomes one point with payload:
      {
        "app_type": "<java|nodejs|python|...>",
        "kind": "<configmap|deploy|service|namespace>",
        "object_name": "<filename without ext>",
        "file_path": "<full path>",
        "file_content": "<text>",
        "timestamp": "<iso>"
      }
    """
    ensure_collection(collection_name)
    for root, dirs, files in os.walk(base_dir):
        for fname in files:
            # only ingest text / yaml files
            if not fname.lower().endswith((".yaml", ".yml", ".txt")):
                continue

            full_path = os.path.join(root, fname)
            try:
                with open(full_path, "r", encoding="utf-8") as fh:
                    content = fh.read()
            except Exception as e:
                print(f"⚠️ Could not read {full_path}: {e}")
                continue

            # derive metadata from path:
            # path example: k8s-templates/python/configmaps/configmap.yaml
            rel = os.path.relpath(full_path, base_dir)
            parts = rel.split(os.sep)  # e.g. ['python','configmaps','configmap.yaml']
            app_type = parts[0].lower() if len(parts) >= 1 else "unknown"
            kind = parts[1].lower() if len(parts) >= 2 else "unknown"
            object_name = os.path.splitext(parts[-1])[0]

            payload = {
                "app_type": app_type,
                "kind": kind,
                "object_name": object_name,
                "file_path": full_path,
                "file_content": content,
                "timestamp": datetime.utcnow().isoformat()
            }

            # deterministic id so re-insert replaces
            point_id = _deterministic_uuid_for_path(full_path)

            # compute embedding (or dummy zeros if embed=False)
            if embed:
                vector = embedder.encode(content).tolist()
            else:
                vector = [0.0] * VECTOR_SIZE

            # delete any existing points with same file_path (safety)
            try:
                client.delete(
                    collection_name=collection_name,
                    points_selector=models.FilterSelector(
                        filter=models.Filter(
                            must=[models.FieldCondition(
                                key="file_path",
                                match=models.MatchValue(value=full_path)
                            )]
                        )
                    )
                )
            except Exception:
                # deletion may fail if filter unsupported; ignore
                pass

            # upsert
            point = models.PointStruct(id=point_id, vector=vector, payload=payload)
            client.upsert(collection_name=collection_name, points=[point])
            print(f"Inserted: app_type={app_type}, kind={kind}, name={object_name}, path={full_path}")


# -------------------------
# Retrieval helpers
# -------------------------
def fetch_k8s_by_app_and_kind(app_type: str, kind: Optional[str] = None, limit: int = 10, collection_name: str = COLLECTION_NAME) -> List[Dict[str, Any]]:
    """
    Return matching points' payloads for an app_type and optional kind.
    """
    # build filter
    must_conditions = [models.FieldCondition(key="app_type", match=models.MatchValue(value=app_type.lower()))]
    if kind:
        must_conditions.append(models.FieldCondition(key="kind", match=models.MatchValue(value=kind.lower())))

    flt = models.Filter(must=must_conditions)
    # using scroll (no vector) to fetch matching points
    response = client.scroll(collection_name=collection_name, limit=limit, with_payload=True, with_vectors=False, scroll_filter=flt)
    points, _ = response
    results = []
    for p in points:
        results.append({"id": p.id, "payload": p.payload})
    return results


def get_k8s_file(app_type: str, kind: str, object_name: str, collection_name: str = COLLECTION_NAME) -> Optional[str]:
    """
    Return file_content for the exact object (or None).
    """
    flt = models.Filter(must=[
        models.FieldCondition(key="app_type", match=models.MatchValue(value=app_type.lower())),
        models.FieldCondition(key="kind", match=models.MatchValue(value=kind.lower())),
        models.FieldCondition(key="object_name", match=models.MatchValue(value=object_name))
    ])
    resp = client.search(collection_name=collection_name, query_vector=[0.0]*VECTOR_SIZE, query_filter=flt, limit=1)
    if resp and len(resp) > 0:
        return resp[0].payload.get("file_content")
    return None


def list_all_k8s(collection_name: str = COLLECTION_NAME, limit: int = 100) -> List[Dict[str, Any]]:
    """
    List up to `limit` stored K8s template payloads.
    """
    points, _ = client.scroll(collection_name=collection_name, limit=limit, with_payload=True, with_vectors=False)
    return [{"id": p.id, "payload": p.payload} for p in points]


# if run as script, simple CLI
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--inject", action="store_true", help="Inject k8s-templates into qdrant")
    parser.add_argument("--list", action="store_true", help="List stored templates")
    parser.add_argument("--base", type=str, default="k8s-templates", help="Base templates dir")
    args = parser.parse_args()
    if args.inject:
        inject_k8s_templates(base_dir=args.base)
    if args.list:
        items = list_all_k8s(limit=200)
        print(json.dumps(items, indent=2))

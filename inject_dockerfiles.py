# Inserting documents to qdrant
from helpers.qdrant_helper import create_dockerfiles_collection, inject_dockerfiles_to_qdrant

create_dockerfiles_collection(collection_name="dockerfiles", vector_size=384)  # 384 for MiniLM
inject_dockerfiles_to_qdrant(base_dir="dockerfiles")


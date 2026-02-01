# scripts/retrieve_k8s_test.py
from helpers.qdrant_k8s_helper import fetch_k8s_by_app_and_kind, get_k8s_file, list_all_k8s
import json

def pretty_print_list(app_type, kind=None):
    items = fetch_k8s_by_app_and_kind(app_type, kind)
    print(f"Found {len(items)} items for app_type={app_type}, kind={kind}")
    for it in items:
        payload = it["payload"]
        print("----")
        print("id:", it["id"])
        print("object_name:", payload.get("object_name"))
        print("file_path:", payload.get("file_path"))
        print("preview:")
        print(payload.get("file_content","")[:400])
        print("----\n")

if __name__ == "__main__":
    # list everything
    all_items = list_all_k8s(limit=200)
    print(f"Total templates in collection: {len(all_items)}\n")

    # example: list python configmaps
    pretty_print_list("python", "configmaps")

    # example: fetch exact file
    content = get_k8s_file("nodejs", "deployments", "deploy")
    if content:
        print("\nExact content for nodejs/deploy:")
        print(content)
    else:
        print("No exact match found for nodejs/deploy")

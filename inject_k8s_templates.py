# scripts/inject_k8s_templates.py
from helpers.qdrant_k8s_helper import inject_k8s_templates

if __name__ == "__main__":
    inject_k8s_templates(base_dir="k8s-templates")

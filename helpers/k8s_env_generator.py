import os
from typing import List, Dict
import yaml
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Reuse your existing qdrant helper functions
from helpers.qdrant_k8s_helper import fetch_k8s_by_app_and_kind


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def _replace_placeholders(yaml_text: str, app_name: str, namespace: str, image_tag: str = None) -> str:
    """
    Replace placeholders in YAML like:
      __APP_NAME__, __NAMESPACE__, __IMAGE_TAG__ (optional)
    """
    if not yaml_text:
        return yaml_text

    updated = (
        yaml_text.replace("__APP_NAME__", app_name)
                 .replace("__NAMESPACE__", namespace)
                 .replace("${APP_NAME}", app_name)
                 .replace("${NAMESPACE}", namespace)
    )
    if image_tag:
        updated = updated.replace("__IMAGE_TAG__", image_tag).replace("${IMAGE_TAG}", image_tag)
    return updated



def _set_namespace_in_yaml(yaml_text: str, namespace: str) -> str:
    """
    Parse YAML (possibly multi-doc), set metadata.namespace to namespace.
    If parsing fails, fallback to original text.
    """
    try:
        docs = list(yaml.safe_load_all(yaml_text))
    except Exception:
        logger.warning("⚠️ Failed to parse YAML for structured namespace update, using fallback text replacement.")
        return yaml_text

    out_docs = []
    for doc in docs:
        if not isinstance(doc, dict):
            out_docs.append(doc)
            continue
        meta = doc.get("metadata", {})
        meta["namespace"] = namespace
        doc["metadata"] = meta
        out_docs.append(doc)

    dumped = ""
    for d in out_docs:
        dumped += yaml.safe_dump(d, sort_keys=False) + "---\n"
    return dumped


def generate_env_yamls(
    app_type: str,
    app_name: str,
    envs: List[str],
    workspace_path: str,
    image_tag: str,
    collection_name: str = "kubernetes_configs"
) -> Dict[str, List[str]]:
    """
    Fetch templates for app_type from Qdrant and create files under:
      <workspace_path>/k8s_configs/<env>/
    Filenames: <kind>-<object_name>.yaml

    Replaces placeholders like:
      __APP_NAME__ → actual app name
      __NAMESPACE__ → appname-env
      __IMAGE_TAG__ → image_tag
    """

    logger.info(f"🚀 Starting YAML generation for app_type={app_type}, app_name={app_name}, envs={envs}")
    results = {}

    # Fetch all templates for given app_type
    templates = fetch_k8s_by_app_and_kind(app_type, kind=None, limit=500, collection_name=collection_name)
    logger.info(f"📦 Retrieved {len(templates)} templates from Qdrant for {app_type}")

    if not templates:
        logger.warning("⚠️ No templates found in Qdrant for this app type.")
        return {env: [] for env in envs}

    for env in envs:
        out_dir = os.path.join(workspace_path, "k8s_configs", env)
        _ensure_dir(out_dir)
        generated_files = []

        namespace = f"{app_name}-{env}"
        logger.info(f"🧩 Generating YAMLs for env={env}, namespace={namespace}")

        for t in templates:
            payload = t.get("payload", {})
            file_content = payload.get("file_content", "")
            kind = payload.get("kind", "unknown")
            object_name = payload.get("object_name", "object")
            filename = f"{object_name}.yaml"
            out_path = os.path.join(out_dir, filename)

            # Step 1: Replace placeholders
            replaced_yaml = _replace_placeholders(file_content, app_name, namespace, image_tag=image_tag)

            # Step 2: Inject structured namespace
            final_yaml = _set_namespace_in_yaml(replaced_yaml, namespace)

            try:
                with open(out_path, "w", encoding="utf-8") as fh:
                    fh.write(final_yaml)
                generated_files.append(out_path)
                logger.debug(f"✅ Generated {out_path}")
            except Exception as e:
                logger.error(f"❌ Failed to write {out_path}: {e}", exc_info=True)
                continue

        results[env] = generated_files

    logger.info(f"✅ YAML generation completed successfully for app={app_name}")
    return results

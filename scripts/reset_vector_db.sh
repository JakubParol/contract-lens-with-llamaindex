#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Usage: scripts/reset_vector_db.sh [--yes]

Clears all vectors from the configured Pinecone index (all namespaces).
Configuration is loaded from .env via contract_lens.config.Settings.

Options:
  --yes    Skip confirmation prompt
EOF
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [[ "${1:-}" != "--yes" ]]; then
  echo "This will delete ALL vectors from the Pinecone index configured in .env."
  read -r -p "Type 'yes' to continue: " CONFIRM
  if [[ "${CONFIRM}" != "yes" ]]; then
    echo "Cancelled."
    exit 1
  fi
fi

PYTHONPATH=src poetry run python - <<'PY'
from contract_lens.config import get_settings
from pinecone import Pinecone

settings = get_settings()
pc = Pinecone(api_key=settings.pinecone_api_key)
index = pc.Index(settings.pinecone_index_name)

stats = index.describe_index_stats()
namespaces = list((stats.get("namespaces") or {}).keys()) or [""]

print(f"Index: {settings.pinecone_index_name}")
print(f"Namespaces to clear: {len(namespaces)}")

for namespace in namespaces:
    index.delete(delete_all=True, namespace=namespace)
    print(f"Cleared namespace: {namespace or '<default>'}")

print("Done.")
print("Current stats:", index.describe_index_stats())
PY

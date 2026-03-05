#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Usage: scripts/show_vector_db_stats.sh

Shows Pinecone vector DB stats for the index configured in .env:
- total vectors
- vectors per namespace
- counts by key metadata values:
  language, source_type, section_type, has_table
- counts by contract_id (detected from local PDF filenames)
EOF
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PYTHONPATH=src poetry run python - <<'PY'
from __future__ import annotations

from collections import Counter

from contract_lens.config import get_settings
from pinecone import Pinecone


def sum_namespace_counts(stats: dict) -> int:
    namespaces = stats.get("namespaces") or {}
    return int(sum((meta or {}).get("vector_count", 0) for meta in namespaces.values()))


def print_section(title: str) -> None:
    print(f"\n{title}")
    print("-" * len(title))


def _as_dict(obj):
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return {}


def iter_ids(index, namespace: str | None = None, page_limit: int = 1000):
    token = None
    while True:
        kwargs = {"limit": page_limit}
        if namespace:
            kwargs["namespace"] = namespace
        if token:
            kwargs["pagination_token"] = token

        resp = index.list_paginated(**kwargs)
        resp_dict = _as_dict(resp)
        vectors = resp_dict.get("vectors") or []
        for item in vectors:
            if isinstance(item, dict):
                vec_id = item.get("id")
            else:
                vec_id = getattr(item, "id", None)
            if vec_id:
                yield vec_id

        pagination = resp_dict.get("pagination") or {}
        token = pagination.get("next")
        if not token:
            break


def normalize_value(field: str, value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value).strip()
    return text.upper() if field == "contract_id" else text.lower()


def scan_metadata(index, namespaces: list[str]) -> tuple[dict[str, Counter], int]:
    fields = ["language", "source_type", "section_type", "has_table", "contract_id"]
    counters = {field: Counter() for field in fields}
    scanned = 0

    for namespace in namespaces:
        batch: list[str] = []
        for vec_id in iter_ids(index, namespace=namespace or None):
            batch.append(vec_id)
            if len(batch) >= 200:
                scanned += process_batch(index, namespace, batch, counters, fields)
                batch.clear()
        if batch:
            scanned += process_batch(index, namespace, batch, counters, fields)

    return counters, scanned


def process_batch(index, namespace: str, ids: list[str], counters: dict[str, Counter], fields: list[str]) -> int:
    kwargs = {"ids": ids}
    if namespace:
        kwargs["namespace"] = namespace

    fetched = index.fetch(**kwargs)
    vectors = getattr(fetched, "vectors", {}) or {}

    processed = 0
    for vec in vectors.values():
        metadata = getattr(vec, "metadata", None) or {}
        for field in fields:
            raw = metadata.get(field)
            key = "<missing>" if raw in (None, "") else normalize_value(field, raw)
            counters[field][key] += 1
        processed += 1

    return processed


settings = get_settings()
pc = Pinecone(api_key=settings.pinecone_api_key)
index = pc.Index(settings.pinecone_index_name)

stats = index.describe_index_stats()
dimension = stats.get("dimension", "n/a")
index_fullness = stats.get("index_fullness", "n/a")
total_vectors = sum_namespace_counts(stats)

print(f"Index: {settings.pinecone_index_name}")
print(f"Dimension: {dimension}")
print(f"Index fullness: {index_fullness}")
print(f"Total vectors: {total_vectors}")

print_section("Namespaces")
namespaces = stats.get("namespaces") or {}
if namespaces:
    for ns, meta in sorted(namespaces.items(), key=lambda x: x[0]):
        print(f"{ns or '<default>'}: {meta.get('vector_count', 0)}")
else:
    print("<none>")

if total_vectors == 0:
    print("\nNo vectors in index. Nothing else to break down.")
    raise SystemExit(0)

scan_namespaces = list(namespaces.keys()) if namespaces else [""]
counters, scanned_vectors = scan_metadata(index, scan_namespaces)

print(f"\nScanned vectors for metadata breakdown: {scanned_vectors}")
if scanned_vectors != total_vectors:
    print("Warning: scanned vector count differs from index stats.")

expected_categories = {
    "language": ["en", "pl"],
    "source_type": ["base", "amendment"],
    "section_type": [
        "scope",
        "payment",
        "termination",
        "confidentiality",
        "liability",
        "sla",
        "penalties",
        "annex",
        "general",
    ],
    "has_table": ["true", "false"],
}

for field, values in expected_categories.items():
    print_section(f"By {field}")
    seen = set()
    for value in values:
        print(f"{value}: {counters[field].get(value, 0)}")
        seen.add(value)
    extras = sorted(k for k in counters[field].keys() if k not in seen and k != "<missing>")
    for extra in extras:
        print(f"{extra}: {counters[field][extra]}")
    if "<missing>" in counters[field]:
        print(f"<missing>: {counters[field]['<missing>']}")

print_section("By contract_id")
contract_counts = counters["contract_id"]
contract_ids = sorted(k for k in contract_counts.keys() if k != "<missing>")

if contract_ids:
    for contract_id in contract_ids:
        print(f"{contract_id}: {contract_counts[contract_id]}")
    if "<missing>" in contract_counts:
        print(f"<missing>: {contract_counts['<missing>']}")
else:
    print("No contract_id metadata found in vectors.")
PY

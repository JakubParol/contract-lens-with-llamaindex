"""Document catalog utilities for metadata-aware counting from Pinecone."""

from __future__ import annotations

from collections import Counter
from typing import Any

from pinecone import Pinecone

from contract_lens.config import Settings


def _as_dict(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return {}


def _iter_vector_ids(index, namespace: str | None = None, page_limit: int = 99):
    token: str | None = None
    while True:
        kwargs: dict[str, Any] = {"limit": page_limit}
        if namespace:
            kwargs["namespace"] = namespace
        if token:
            kwargs["pagination_token"] = token

        response = index.list_paginated(**kwargs)
        payload = _as_dict(response)
        vectors = payload.get("vectors") or []

        for item in vectors:
            if isinstance(item, dict):
                vector_id = item.get("id")
            else:
                vector_id = getattr(item, "id", None)
            if vector_id:
                yield vector_id

        pagination = payload.get("pagination") or {}
        token = pagination.get("next")
        if not token:
            break


def _normalize_source_type(raw: Any) -> str:
    value = str(raw or "").strip().lower()
    if value in ("base", "amendment"):
        return value
    return "unknown"


def _normalize_language(raw: Any) -> str:
    value = str(raw or "").strip().lower()
    if value in ("en", "pl"):
        return value
    return "unknown"


def _normalize_document_type(raw: Any, source_type: str) -> str:
    value = str(raw or "").strip().lower()
    if value in ("contract", "amendment"):
        return value
    if source_type == "base":
        return "contract"
    if source_type == "amendment":
        return "amendment"
    return "unknown"


def summarize_document_catalog(settings: Settings) -> dict[str, Any]:
    """Scan vector metadata and return document-level counts.

    Counting is deduplicated by file name (or metadata fallback key) to avoid
    chunk-level overcounting.
    """
    pc = Pinecone(api_key=settings.pinecone_api_key)
    index = pc.Index(settings.pinecone_index_name)
    stats = index.describe_index_stats()

    namespaces = list((stats.get("namespaces") or {}).keys()) or [""]
    documents: dict[str, dict[str, str]] = {}

    for namespace in namespaces:
        batch: list[str] = []
        for vector_id in _iter_vector_ids(index, namespace=namespace or None):
            batch.append(vector_id)
            if len(batch) >= 200:
                _scan_batch(index, namespace, batch, documents)
                batch.clear()
        if batch:
            _scan_batch(index, namespace, batch, documents)

    totals = Counter()
    by_language: dict[str, dict[str, int]] = {}
    base_contract_ids: set[str] = set()

    for doc in documents.values():
        source_type = doc["source_type"]
        language = doc["language"]
        contract_id = doc["contract_id"]

        totals["documents"] += 1
        if source_type == "base":
            totals["contracts"] += 1
            if contract_id != "UNKNOWN":
                base_contract_ids.add(contract_id)
        elif source_type == "amendment":
            totals["amendments"] += 1

        if language not in by_language:
            by_language[language] = {
                "documents": 0,
                "contracts": 0,
                "amendments": 0,
                "unique_contract_ids": 0,
            }

        lang_stats = by_language[language]
        lang_stats["documents"] += 1
        if source_type == "base":
            lang_stats["contracts"] += 1
        elif source_type == "amendment":
            lang_stats["amendments"] += 1

    # Compute unique contract IDs per language for base contracts
    for language in by_language:
        lang_contract_ids = {
            doc["contract_id"]
            for doc in documents.values()
            if doc["language"] == language and doc["source_type"] == "base" and doc["contract_id"] != "UNKNOWN"
        }
        by_language[language]["unique_contract_ids"] = len(lang_contract_ids)

    return {
        "total_documents": totals["documents"],
        "contracts": totals["contracts"],
        "amendments": totals["amendments"],
        "unique_contract_ids": len(base_contract_ids),
        "by_language": by_language,
    }


def _scan_batch(index, namespace: str, ids: list[str], documents: dict[str, dict[str, str]]) -> None:
    kwargs: dict[str, Any] = {"ids": ids}
    if namespace:
        kwargs["namespace"] = namespace

    fetched = index.fetch(**kwargs)
    vectors = getattr(fetched, "vectors", {}) or {}

    for vector in vectors.values():
        metadata = getattr(vector, "metadata", None) or {}
        filename = str(metadata.get("file_name") or metadata.get("filename") or "").strip()
        contract_id = str(metadata.get("contract_id") or "UNKNOWN").upper()
        source_type = _normalize_source_type(metadata.get("source_type"))
        language = _normalize_language(metadata.get("language"))
        document_type = _normalize_document_type(metadata.get("document_type"), source_type)
        version = str(metadata.get("version") or "").strip()
        effective_date = str(metadata.get("effective_date") or "").strip()

        if filename:
            key = f"file:{filename.lower()}"
        else:
            key = f"meta:{contract_id}:{source_type}:{version}:{effective_date}"

        if key not in documents:
            documents[key] = {
                "contract_id": contract_id,
                "source_type": source_type,
                "document_type": document_type,
                "language": language,
            }

"""Amendment-aware retriever with post-retrieval deduplication.

Wraps a standard LlamaIndex vector retriever and adds a deduplication step
that keeps only the latest version of each clause, preventing stale base
contract terms from crowding out amendments in the top-K results.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.vector_stores import MetadataFilters

logger = logging.getLogger(__name__)


def _grouping_key(node: NodeWithScore) -> tuple[str, str, str]:
    """Build a grouping key from node metadata.

    Groups by (contract_id, section_type, clause_number).
    Falls back gracefully when metadata fields are missing.
    """
    meta = node.metadata or {}
    contract_id = str(meta.get("contract_id", "")).strip().upper() or "UNKNOWN"
    section_type = str(meta.get("section_type", "")).strip().lower() or "general"
    clause_number = str(meta.get("clause_number", "")).strip()
    return (contract_id, section_type, clause_number)


def _version_sort_key(node: NodeWithScore) -> tuple[int, str]:
    """Return (version_int, effective_date) for sorting within a group."""
    meta = node.metadata or {}
    try:
        version = int(meta.get("version", 0))
    except (ValueError, TypeError):
        version = 0
    effective_date = str(meta.get("effective_date", "")).strip()
    return (version, effective_date)


def _max_version(nodes: list[NodeWithScore]) -> int:
    """Return the highest version number across all nodes."""
    max_v = 0
    for node in nodes:
        try:
            v = int((node.metadata or {}).get("version", 0))
        except (ValueError, TypeError):
            v = 0
        if v > max_v:
            max_v = v
    return max_v or 1  # avoid division by zero


def deduplicate_by_version(
    nodes: list[NodeWithScore],
    top_k: int = 8,
    version_boost: float = 0.05,
) -> list[NodeWithScore]:
    """Deduplicate nodes: keep only the latest version per (contract_id, section_type, clause_number).

    Args:
        nodes: Raw nodes from vector retriever (over-fetched).
        top_k: Final number of nodes to return.
        version_boost: Small score bonus proportional to version recency.
            Set to 0.0 to disable.

    Returns:
        Deduplicated and re-scored list, truncated to top_k.
    """
    if not nodes:
        return []

    # Group by (contract_id, section_type, clause_number)
    groups: dict[tuple[str, str, str], list[NodeWithScore]] = defaultdict(list)
    for node in nodes:
        key = _grouping_key(node)
        groups[key].append(node)

    # Within each group, keep only nodes from the highest version
    deduplicated: list[NodeWithScore] = []
    for key, group_nodes in groups.items():
        max_ver = max(_version_sort_key(n)[0] for n in group_nodes)
        latest = [n for n in group_nodes if _version_sort_key(n)[0] == max_ver]
        deduplicated.extend(latest)

        pruned_count = len(group_nodes) - len(latest)
        if pruned_count > 0:
            logger.debug(
                "Group %s: kept %d node(s) (v%d), pruned %d older",
                key, len(latest), max_ver, pruned_count,
            )

    # Re-score with optional version boost
    if version_boost > 0:
        global_max_v = _max_version(deduplicated)
        for node in deduplicated:
            try:
                v = int((node.metadata or {}).get("version", 0))
            except (ValueError, TypeError):
                v = 0
            boost = version_boost * (v / global_max_v)
            node.score = (node.score or 0.0) + boost

    # Sort by score descending and truncate
    deduplicated.sort(key=lambda n: n.score or 0.0, reverse=True)
    return deduplicated[:top_k]


class AmendmentAwareRetriever(BaseRetriever):
    """Retriever that over-fetches from a vector index, then deduplicates by version.

    Ensures the LLM context contains the latest version of each clause
    rather than stale base contract terms that may score higher on similarity.
    """

    def __init__(
        self,
        index: Any,
        top_k: int = 8,
        fetch_k: int | None = None,
        version_boost: float = 0.05,
        filters: MetadataFilters | None = None,
    ):
        super().__init__()
        self._top_k = top_k
        self._fetch_k = fetch_k or top_k * 3
        self._version_boost = version_boost

        self._inner_retriever = index.as_retriever(
            similarity_top_k=self._fetch_k,
            filters=filters,
        )

    def _retrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        """Retrieve nodes with amendment-aware deduplication."""
        # Over-fetch
        raw_nodes = self._inner_retriever.retrieve(query_bundle)
        logger.debug("Over-fetched %d nodes (fetch_k=%d)", len(raw_nodes), self._fetch_k)

        # Deduplicate
        result = deduplicate_by_version(
            raw_nodes,
            top_k=self._top_k,
            version_boost=self._version_boost,
        )
        logger.debug("After dedup: %d nodes (top_k=%d)", len(result), self._top_k)
        return result

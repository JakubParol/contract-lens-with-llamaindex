# Amendment Override

How Contract Lens ensures the latest version of a clause is returned, not stale base contract terms.

## The Problem

Standard vector similarity search has no concept of document versioning. When a base contract and its amendments are all indexed, a query like "What is the hourly rate?" may return the **base contract chunk** ($250/hr) instead of the **latest amendment** ($310/hr) because:

1. **Base contracts are more verbose** — more surrounding context means richer embeddings that often score higher on cosine similarity.
2. **Amendments are terse** — "Section 3.1 is amended to read: $310/hr" has less text, potentially lower similarity to a natural-language question.
3. **Top-K slots are wasted** — the same clause across 3 versions = 3 chunks consuming top-K slots, pushing out other relevant content.

With a standard retriever (top_k=8), there is no guarantee that amendment chunks even appear in the results.

## The Solution: AmendmentAwareRetriever

`AmendmentAwareRetriever` wraps the standard LlamaIndex vector retriever and adds a post-retrieval deduplication step.

### Algorithm

```
Query
  |
  v
[1] Over-fetch: retrieve fetch_k chunks (default: 3x top_k = 24)
  |
  v
[2] Group by (contract_id, section_type, clause_number)
  |
  v
[3] Deduplicate: within each group, keep only the highest version
  |
  v
[4] Re-score: apply version_boost to gently prefer newer documents
  |
  v
[5] Truncate to final top_k (default: 8)
  |
  v
Return to query engine for LLM synthesis
```

### Step Details

**Step 1 — Over-fetch.** We retrieve 3x more chunks than needed to ensure amendment chunks have a chance to appear even if they score lower on similarity.

**Step 2 — Group.** Chunks are grouped by `(contract_id, section_type, clause_number)`. Missing `clause_number` falls back to `(contract_id, section_type)`. Missing both uses `(contract_id, "general")`.

**Step 3 — Deduplicate.** Within each group, only chunks from the highest `version` number survive. If versions are equal, `effective_date` is used as tiebreaker. This removes stale base contract chunks when a newer amendment covers the same clause.

**Step 4 — Re-score.** A small bonus is added to each node's similarity score proportional to its version recency:

```
adjusted_score = original_score + version_boost * (version / max_version)
```

Default `version_boost = 0.05` — small enough to not override strong similarity differences, but enough to break ties in favor of newer documents.

**Step 5 — Truncate.** The deduplicated, re-scored list is sorted by score and truncated to `top_k`.

### Configuration

| Parameter | Default | Description |
|---|---|---|
| `top_k` | 8 | Final number of chunks returned to the LLM |
| `fetch_k` | `3 * top_k` | Number of chunks to over-fetch from Pinecone |
| `version_boost` | 0.05 | Score bonus for version recency (0.0 = disabled) |

### Example

Query: "What is the current hourly rate for ITSVC-001?"

**Without AmendmentAwareRetriever** (standard similarity):

| Rank | Score | Version | Text |
|------|-------|---------|------|
| 1 | 0.92 | v1 (base) | Hourly rate: $250... |
| 2 | 0.88 | v2 (amendment) | Rate amended to $285... |
| 3 | 0.85 | v3 (amendment) | Rate amended to $310... |

The LLM sees v1 first and may use the stale $250 rate.

**With AmendmentAwareRetriever**:

| Rank | Score | Version | Text |
|------|-------|---------|------|
| 1 | 0.90 | v3 (amendment) | Rate amended to $310... |

v1 and v2 are pruned. Only v3 remains. The LLM correctly reports $310/hr.

## Integration

The retriever is integrated into `build_query_engine()` in `src/contract_lens/retrieval/query_engine.py`. All existing metadata filters (language, contract_id, section_type, etc.) are applied at the Pinecone level **before** the over-fetch — so filtering and deduplication compose cleanly.

The `search_contracts` agent tool requires no changes — it calls `query_contracts()` which calls `build_query_engine()`, so the agent automatically benefits from amendment-aware retrieval.

## Source Files

- `src/contract_lens/retrieval/amendment_retriever.py` — `AmendmentAwareRetriever` class and `deduplicate_by_version()` function
- `src/contract_lens/retrieval/query_engine.py` — integration with query engine

## Known Limitations

- **Relies on metadata** — deduplication requires `contract_id`, `version`, `section_type`, and `clause_number` in chunk metadata. If metadata is missing or incorrect, deduplication will be less effective.
- **Section-level granularity** — deduplication groups by section, not by individual sentence. If an amendment changes one sentence in a long section, the entire base section is still pruned.
- **No cross-encoder reranking** — the version boost is a simple heuristic. A cross-encoder reranker could provide more nuanced relevance scoring (possible future enhancement).

## Navigation

- [INDEX.md](INDEX.md)
- [README.md](../README.md)

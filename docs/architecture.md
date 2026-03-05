# Architecture

## Overview

The system has three main pipelines: **ingestion**, **retrieval**, and **agent**.

```
┌─────────────────────────────────────────────────────────┐
│                    INGESTION PIPELINE                    │
│                                                         │
│  Scanned PDFs ──▶ Azure DI OCR* ──▶ Documents           │
│       │            (* falls back to SimpleDirectoryReader│
│       ▼              if Azure DI not configured)        │
│  ContractNodeParser (structure-aware chunking)          │
│       │                                                 │
│       ▼                                                 │
│  AzureOpenAIEmbedding ──▶ PineconeVectorStore (upsert)  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   RETRIEVAL PIPELINE                     │
│                                                         │
│  Query ──▶ VectorStoreIndex (Pinecone) ──▶ Over-fetch   │
│       │                                                 │
│       ▼                                                 │
│  AmendmentAwareRetriever (dedup by version) ──▶ Top-K   │
│       │                                                 │
│       ▼                                                 │
│  RetrieverQueryEngine ──▶ LLM synthesis ──▶ Answer      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                     AGENT LAYER                          │
│                                                         │
│  User message ──▶ LangGraph (ReAct) ──▶ Decide action   │
│                        │                                │
│                  ┌─────┴──────┐                         │
│                  │            │                         │
│              Respond    search_contracts (tool)          │
│              directly   ──▶ LlamaIndex QueryEngine      │
│                              ──▶ Return context         │
│                              ──▶ LLM final answer       │
└─────────────────────────────────────────────────────────┘

All pipelines traced via LangFuse (LlamaIndexInstrumentor + LangChain CallbackHandler)
```

## Component Responsibilities

### `src/contract_lens/config.py`
Central configuration via `pydantic-settings`. Loads all API keys, endpoints, and model deployments from `.env`.

### `src/contract_lens/observability.py`
Initializes LangFuse tracing for both LlamaIndex and LangGraph. Single `init_observability()` entry point.

### `src/contract_lens/ingestion/reader.py`
- `load_documents()` — loads PDFs with Azure Document Intelligence OCR when configured (endpoint + key in `.env`)
- Falls back to `SimpleDirectoryReader` when Azure DI is not configured
- OCR uses `prebuilt-layout` model, returns markdown-formatted text

### `src/contract_lens/ingestion/pipeline.py`
- Loads scanned PDFs from `data/scans/` via `reader.load_documents()`
- Extracts amendment-aware metadata from filenames: `contract_id`, `source_type`, `document_type`, `language`, `version`, `effective_date`
- Chunks with `ContractNodeParser` (structure-aware — splits at section boundaries, enriches with `section_type`, `section_name`, `has_table`, `clause_number`)
- Embeds via Azure OpenAI embedding model
- Upserts to Pinecone with all metadata

### `src/contract_lens/retrieval/amendment_retriever.py`
- `AmendmentAwareRetriever` wraps the standard vector retriever
- Over-fetches 3x, groups by `(contract_id, section_type, clause_number)`, deduplicates by version
- Ensures the LLM context contains only the latest version of each clause
- `deduplicate_by_version()` is also usable standalone for testing and notebooks

### `src/contract_lens/retrieval/query_engine.py`
- Connects to existing Pinecone index
- Builds `VectorStoreIndex` with `AmendmentAwareRetriever` and `RetrieverQueryEngine`
- Supports metadata filtering (by language, document type, section type, etc.)
- Uses Azure OpenAI LLM for response synthesis

### `src/contract_lens/retrieval/catalog.py`
- `summarize_document_catalog()` — metadata-aware document counting (not chunk counting)
- Groups Pinecone vectors by `(contract_id, source_type, version)` to count unique documents
- Returns breakdown by language, contract vs. amendment counts, unique contract IDs

### `src/contract_lens/agent/`
- **`state.py`** — LangGraph state schema (messages, context)
- **`tools.py`** — `search_contracts` tool wrapping the LlamaIndex query engine; `count_contract_documents` tool for metadata-aware document counting
- **`graph.py`** — ReAct-style graph: LLM node decides whether to call retrieval tool or respond directly

## Synthetic Data Pipeline

Agreements and their amendments are generated and degraded before ingestion:

```
scripts/generate_agreements.py          scripts/simulate_scans.py
        │                                       │
        ▼                                       ▼
  fpdf2 + DejaVu Sans               pdf2image + Pillow
  (Unicode EN/PL support)            (rotation, noise, blur)
        │                                       │
        ▼                                       ▼
  data/agreements/*.pdf  ──────────▶  data/scans/*.pdf
  (9 PDFs: 5 bases +                  (9 scan-simulated PDFs)
   4 amendments)
```

Filename convention encodes metadata for ingestion:
```
{nn}_{contract_id}_{source_type}_{lang}_v{version}_{effective_date}.pdf
```
- `contract_id` → links base contracts with their amendments (e.g., `ITSVC-001`)
- `source_type` → `base` or `amendment`
- `lang` → `en` or `pl`
- `version` → sequential version number (`v1` = base, `v2` = first amendment, etc.)
- `effective_date` → date from which terms apply

## Data Flow

1. Generate synthetic agreements → `data/agreements/`
2. Simulate scans (rotation, noise, blur) → `data/scans/`
3. Ingestion pipeline processes scans into Pinecone vectors
4. User asks a question via CLI (`scripts/chat.py`) or notebook
5. LangGraph agent receives the question
6. Agent decides to call `search_contracts` tool
7. Tool queries Pinecone via LlamaIndex, returns synthesized context
8. Agent formulates final answer using the retrieved context
9. All steps are traced in LangFuse

## Navigation

- [INDEX.md](INDEX.md)
- [README.md](../README.md)

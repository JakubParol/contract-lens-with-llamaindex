# Architecture

## Overview

The system has three main pipelines: **ingestion**, **retrieval**, and **agent**.

```
┌─────────────────────────────────────────────────────────┐
│                    INGESTION PIPELINE                    │
│                                                         │
│  Scanned PDFs ──▶ SimpleDirectoryReader ──▶ OCR/Parse   │
│       │                                                 │
│       ▼                                                 │
│  SentenceSplitter (chunking with metadata)              │
│       │                                                 │
│       ▼                                                 │
│  AzureOpenAIEmbedding ──▶ PineconeVectorStore (upsert)  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   RETRIEVAL PIPELINE                     │
│                                                         │
│  Query ──▶ VectorStoreIndex (Pinecone) ──▶ Top-K docs   │
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

### `src/contract_lens/ingestion/pipeline.py`
- Loads scanned PDFs from `data/scans/`
- Chunks with `SentenceSplitter` (tuned for contract text — longer chunks to preserve clause context)
- Embeds via Azure OpenAI embedding model
- Upserts to Pinecone with metadata: `filename`, `language` (en/pl), `document_type` (agreement/annex), `page_number`

### `src/contract_lens/retrieval/query_engine.py`
- Connects to existing Pinecone index
- Builds `VectorStoreIndex` and `RetrieverQueryEngine`
- Supports metadata filtering (by language, document type)
- Uses Azure OpenAI LLM for response synthesis

### `src/contract_lens/agent/`
- **`state.py`** — LangGraph state schema (messages, context)
- **`tools.py`** — `search_contracts` tool wrapping the LlamaIndex query engine
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

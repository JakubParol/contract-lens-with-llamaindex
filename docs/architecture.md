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

## Data Flow

1. Scanned PDFs (simulated from generated agreements) sit in `data/scans/`
2. Ingestion pipeline processes them into Pinecone vectors
3. User asks a question via CLI (`scripts/chat.py`)
4. LangGraph agent receives the question
5. Agent decides to call `search_contracts` tool
6. Tool queries Pinecone via LlamaIndex, returns synthesized context
7. Agent formulates final answer using the retrieved context
8. All steps are traced in LangFuse

## Navigation

- [INDEX.md](INDEX.md)
- [README.md](../README.md)

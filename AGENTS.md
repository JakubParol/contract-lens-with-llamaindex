# AGENTS.md — Contract Lens with LlamaIndex

## Project Context

Reference architecture / POC demonstrating a RAG-based contract analysis pipeline. The target audience is a big data consulting company's delivery teams who need to adopt LLM patterns (RAG, agents) for client projects — particularly in the document/agreement processing domain.

**Real-world use case:** A client with large volumes of scanned agreements (contracts, annexes, NDAs, SLAs) in English and Polish needs to query and extract information from them.

## Scope

This repo covers:
- Document ingestion (OCR, chunking, embedding, vector storage)
- RAG retrieval over contract data
- Conversational agent with tool-based retrieval
- Observability / tracing across both frameworks
- Synthetic test data generation (scanned agreement PDFs)

This repo does NOT cover:
- Production deployment (no Docker, no CI/CD)
- Authentication or multi-tenancy
- Fine-tuning or custom model training

## Required Reading Before Making Changes

1. [docs/INDEX.md](docs/INDEX.md) — documentation overview
2. [docs/architecture.md](docs/architecture.md) — system design and data flow
3. [docs/tech-stack.md](docs/tech-stack.md) — technology choices and rationale
4. [docs/synthetic-data.md](docs/synthetic-data.md) — how test agreements are generated

## Rules and Constraints

- **Python 3.12** — do not upgrade to 3.13 (ecosystem compatibility)
- **Poetry** for dependency management — no pip, no requirements.txt
- **LlamaIndex** for all document processing and RAG — do not use LangChain's document loaders or retrievers
- **LangGraph** only for the agent orchestration layer — keep it minimal (ReAct pattern)
- **Azure AI Foundry** models — all LLM and embedding calls go through Azure OpenAI endpoints directly (no proxy layer)
- **LangFuse** for observability — use `LlamaIndexInstrumentor` (not the deprecated callback handler) and `langfuse.langchain.CallbackHandler` for LangGraph
- No hardcoded API keys — everything via `.env` and `pydantic-settings`
- Agreements in both English and Polish — metadata must track language
- **Amendments override base contract terms** — metadata must include `contract_id`, `source_type` (base/amendment), `effective_date`, `version`. Filenames encode this metadata for automatic detection during ingestion.
- **Structure-aware chunking** — `ContractNodeParser` in `src/contract_lens/ingestion/node_parser.py` splits at section boundaries and adds `section_type` (controlled vocabulary: scope, payment, termination, confidentiality, liability, sla, penalties, annex, general), `section_name`, `has_table`, `clause_number` metadata.
- **Metadata-first retrieval** — query engine and agent tool support filtering by `section_type`, `has_table`, `clause_number` in addition to `language`, `contract_id`, `source_type`.

## Key Patterns

- **Ingestion and retrieval are separate concerns** — ingestion pipeline writes to Pinecone, query engine reads from it. They share config, not state.
- **The agent uses LlamaIndex as a tool** — LangGraph agent calls a `search_contracts` tool that wraps a LlamaIndex `RetrieverQueryEngine`. The frameworks don't deeply interleave.
- **Config is centralized** — `src/contract_lens/config.py` using `pydantic-settings`, loaded from `.env`.

## Navigation

- [README.md](README.md)
- [docs/INDEX.md](docs/INDEX.md)

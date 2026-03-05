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
5. [docs/smart-chunking.md](docs/smart-chunking.md) — structure-aware chunking and metadata-first retrieval
6. [docs/amendment-override.md](docs/amendment-override.md) — amendment-aware retrieval algorithm

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
- **OCR is optional** — `src/contract_lens/ingestion/reader.py` uses Azure Document Intelligence when `AZURE_DOC_INTELLIGENCE_ENDPOINT` and `AZURE_DOC_INTELLIGENCE_KEY` are set in `.env`. Without them, it falls back to `SimpleDirectoryReader` (works for text-based PDFs but not scans).
- **Structure-aware chunking** — `ContractNodeParser` in `src/contract_lens/ingestion/node_parser.py` splits at section boundaries and adds `section_type` (controlled vocabulary: scope, payment, termination, confidentiality, liability, sla, penalties, annex, general), `section_name`, `has_table`, `clause_number` metadata.
- **Metadata-first retrieval** — query engine and agent tool support filtering by `section_type`, `has_table`, `clause_number` in addition to `language`, `contract_id`, `source_type`.

## Key Patterns

- **Ingestion and retrieval are separate concerns** — ingestion pipeline writes to Pinecone, query engine reads from it. They share config, not state.
- **The agent uses LlamaIndex as a tool** — LangGraph agent calls a `search_contracts` tool that wraps a LlamaIndex `RetrieverQueryEngine`. The frameworks don't deeply interleave.
- **Amendment-aware retrieval** — `AmendmentAwareRetriever` in `src/contract_lens/retrieval/amendment_retriever.py` wraps the standard vector retriever with post-retrieval deduplication. Over-fetches 3x, groups by `(contract_id, section_type, clause_number)`, keeps only the latest version, applies a small version boost, and truncates. This ensures the LLM sees current terms, not stale base contract clauses.
- **Config is centralized** — `src/contract_lens/config.py` using `pydantic-settings`, loaded from `.env`.

## Navigation

- [README.md](README.md)
- [docs/INDEX.md](docs/INDEX.md)

## Execution Workflow (mc + gh)

Trigger: apply this flow whenever the user asks to implement/code a `US`, `Task`, or `Bug`.

Tools:
- Planning/work tracking: `mc` CLI
- GitHub flow/PR/review: `gh` CLI

Steps:
1. Checkout `main`.
2. Pull latest from remote.
3. Read target `US`/`Task`/`Bug` via `mc`.
4. Build implementation plan from the `US` and create child tasks in `mc` under that `US`.
   - `Task` and `Bug` should be implemented without creating child tasks.
5. Create and checkout branch named: `<work-item-code>-<short-description>`.
6. Set work item status to `IN_PROGRESS` via `mc`.
7. Implement.
   - If child tasks exist: execute task-by-task and move each task `IN_PROGRESS` -> `DONE` in `mc`.
8. Commit changes and create PR via `gh`.
9. Move `US`/`Task`/`Bug` status to `CODE_REVIEW` via `mc`.
10. Perform code review and add PR comments via `gh`.
11. Resolve all review comments and mark them resolved via `gh`.
12. Merge PR.
13. Locally checkout `main` and pull latest.
14. Move final `US`/`Task`/`Bug` status to `DONE` via `mc`.

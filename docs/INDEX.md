# Documentation Index

All project documentation for Contract Lens with LlamaIndex.

## Docs

| Document | Description |
|---|---|
| [architecture.md](architecture.md) | System design, data flow, component responsibilities |
| [tech-stack.md](tech-stack.md) | Technology choices, versions, and rationale |
| [synthetic-data.md](synthetic-data.md) | Synthetic agreement generation strategy |
| [azure-vector-options.md](azure-vector-options.md) | Azure-native vector DB alternatives to Pinecone |
| [smart-chunking.md](smart-chunking.md) | Structure-aware chunking and metadata-first retrieval |
| [amendment-override.md](amendment-override.md) | Amendment-aware retrieval with post-retrieval deduplication |

## Notebooks

| Notebook | Description |
|---|---|
| [01_generate_data.ipynb](../notebooks/01_generate_data.ipynb) | Generate synthetic PDFs and simulate scans |
| [02_ingestion.ipynb](../notebooks/02_ingestion.ipynb) | Step-by-step LlamaIndex ingestion to Pinecone |
| [03_agent_demo.ipynb](../notebooks/03_agent_demo.ipynb) | LangGraph agent with example contract queries |
| [04_smart_chunking_demo.ipynb](../notebooks/04_smart_chunking_demo.ipynb) | Structure-aware chunking and metadata-first retrieval |
| [05_amendment_override_demo.ipynb](../notebooks/05_amendment_override_demo.ipynb) | Amendment-aware retrieval before/after comparison |

## Scripts

| Script | Description |
|---|---|
| `scripts/generate_agreements.py` | Generate 5 synthetic agreement PDFs (EN + PL) |
| `scripts/simulate_scans.py` | Apply scan effects (rotation, noise, blur) to PDFs |
| `scripts/ingest.py` | Run ingestion pipeline CLI |
| `scripts/chat.py` | Interactive agent CLI |
| `scripts/reset_vector_db.sh` | Clear all vectors from Pinecone index |
| `scripts/show_vector_db_stats.sh` | Show vector DB stats and metadata breakdown |
| `scripts/tui.py` | Interactive workflow and maintenance menu |

## Navigation

- [README.md](../README.md)
- [AGENTS.md](../AGENTS.md)

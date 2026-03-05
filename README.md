# Contract Lens with LlamaIndex

RAG pipeline and conversational agent for analyzing scanned agreements (contracts, NDAs, SLAs, annexes) in English and Polish. Built as a reference architecture demonstrating LlamaIndex + LangGraph + Pinecone + LangFuse on Azure AI Foundry.

## Architecture

```
Scanned PDFs (EN/PL)
        │
        ▼
┌─────────────────────┐
│  LlamaIndex          │
│  Ingestion Pipeline  │
│  (OCR → Smart Chunk →│
│   Embed → Upsert)   │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Pinecone            │
│  Vector Store        │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐     ┌──────────────┐
│  LangGraph Agent     │────▶│  LangFuse    │
│  (ReAct + RAG tool)  │     │  Tracing     │
└────────┬────────────┘     └──────────────┘
         │
         ▼
    User / Chat CLI

Models: Azure AI Foundry (direct)
```

## Tech Stack

| Layer | Technology |
|---|---|
| RAG Framework | LlamaIndex |
| Agent Framework | LangGraph |
| Vector Store | Pinecone |
| LLM / Embeddings | Azure AI Foundry (OpenAI models, direct) |
| OCR (optional) | Azure Document Intelligence |
| Observability | LangFuse |
| Language | Python 3.12, Poetry |

## Repository Structure

```
contract-lens-with-llamaindex/
├── src/contract_lens/
│   ├── config.py              # Environment configuration
│   ├── observability.py       # LangFuse tracing setup
│   ├── ingestion/             # LlamaIndex: load → chunk → embed → Pinecone
│   ├── retrieval/             # Query engine over Pinecone index
│   └── agent/                 # LangGraph agent with RAG tools
│
├── scripts/
│   ├── generate_agreements.py # Synthetic agreement PDF generator
│   ├── simulate_scans.py      # Apply scan effects (noise, rotation)
│   ├── ingest.py              # Run ingestion pipeline
│   ├── chat.py                # Interactive agent CLI
│   ├── reset_vector_db.sh     # Clear all vectors from Pinecone index
│   ├── show_vector_db_stats.sh # Show vector DB stats and metadata breakdown
│   └── tui.py                 # Interactive workflow/maintenance menu
│
├── data/
│   ├── agreements/            # Generated clean PDFs
│   └── scans/                 # Scan-simulated PDFs
│
├── notebooks/                 # Step-by-step demos
└── docs/                      # Project documentation
```

## Getting Started

### Prerequisites

- Python 3.12+
- [Poetry](https://python-poetry.org/)
- Pinecone account and API key
- Azure AI Foundry deployment (GPT-4 + embedding model)
- Azure Document Intelligence resource (optional, for OCR of scanned PDFs)
- LangFuse account (optional, for observability)

### Setup

```bash
# Clone
git clone https://github.com/JakubParol/contract-lens-with-llamaindex.git
cd contract-lens-with-llamaindex

# Install dependencies
poetry install

# Configure environment
cp .env.example .env
# Edit .env with your API keys
# For OCR of scanned PDFs, add Azure Document Intelligence keys (optional)
```

### Usage

```bash
# Optional: run interactive menu for workflow + maintenance
poetry run python scripts/tui.py

# 1. Generate synthetic agreements
poetry run python scripts/generate_agreements.py

# 2. Simulate scans (add noise, rotation)
poetry run python scripts/simulate_scans.py

# 3. Ingest into Pinecone
poetry run python scripts/ingest.py

# 4. Chat with the agent
poetry run python scripts/chat.py
```

## Notebooks

| # | Notebook | Description |
|---|----------|-------------|
| 1 | [01_generate_data.ipynb](notebooks/01_generate_data.ipynb) | Generate synthetic agreement PDFs and simulate scans |
| 2 | [02_ingestion.ipynb](notebooks/02_ingestion.ipynb) | Step-by-step LlamaIndex ingestion pipeline to Pinecone |
| 3 | [03_agent_demo.ipynb](notebooks/03_agent_demo.ipynb) | Interactive LangGraph agent with example contract queries |
| 4 | [04_smart_chunking_demo.ipynb](notebooks/04_smart_chunking_demo.ipynb) | Structure-aware chunking and metadata-first retrieval |
| 5 | [05_amendment_override_demo.ipynb](notebooks/05_amendment_override_demo.ipynb) | Amendment-aware retrieval before/after comparison |

## Smart Chunking

The ingestion pipeline uses a custom `ContractNodeParser` that detects section boundaries (numbered sections, annexes, amendments, Polish legal markers like §, Rozdział, Artykuł) and enriches each chunk with structural metadata:

- **`section_type`**: controlled vocabulary — `scope`, `payment`, `termination`, `confidentiality`, `liability`, `sla`, `penalties`, `annex`, `general`
- **`has_table`**: whether the chunk contains a table (pricing schedule, SLA metrics, etc.)
- **`clause_number`**: first clause number in the chunk (e.g. "3.1")

These metadata fields enable **metadata-first retrieval** — filtering by section type or table presence before semantic search, improving precision for targeted queries.

See [docs/smart-chunking.md](docs/smart-chunking.md) for details.

## Amendment Override

When a contract has amendments, standard similarity search may return stale base contract terms instead of the latest amendment — because base contracts are more verbose and score higher on cosine similarity.

The `AmendmentAwareRetriever` solves this with a post-retrieval deduplication step:

1. **Over-fetch** 3x more chunks than needed
2. **Group** by `(contract_id, section_type, clause_number)`
3. **Deduplicate** — keep only the latest version in each group
4. **Re-score** with a small version boost
5. **Truncate** to final top-K

This ensures the LLM always sees the most current terms. For example, querying "What is the hourly rate for ITSVC-001?" returns $310/hr (amendment v3) instead of $250/hr (base contract).

See [docs/amendment-override.md](docs/amendment-override.md) for the full algorithm and configuration.

## Synthetic Agreements

The project generates 5 base contracts and 4 amendments to test **amendment-aware RAG** — where amendments override specific clauses from the base contract and the system must return the latest effective terms.

| Contract ID | Type | Language | Documents |
|-------------|------|----------|-----------|
| ITSVC-001 | IT Service Agreement | EN | Base (2025-01-15) + Amendment 1 (2025-07-01) + Amendment 2 (2026-01-01) |
| NDA-001 | Mutual NDA | EN | Base only (2025-03-01) |
| LEASE-001 | Office Lease | PL | Base (2025-02-10) + Amendment 1 (2025-09-01) |
| SLA-001 | Cloud SLA | EN | Base (2025-04-01) + Amendment 1 (2025-10-01) |
| EMP-001 | Employment Contract | PL | Base only (2025-05-01) |

**Amendment examples:**
- ITSVC-001: hourly rate $250 → $285 → $310 (across 3 versions), new AI/ML service tier added in v3
- LEASE-001: rent 25,000 PLN → 28,500 PLN, parking spaces added
- SLA-001: P1 response time 15 min → 5 min, credit cap 30% → 50%

Filenames encode metadata: `{nn}_{contract_id}_{source_type}_{lang}_v{version}_{effective_date}.pdf`

PDFs are generated with `fpdf2` (DejaVu Sans for Unicode/Polish), then degraded with Pillow to simulate scanned documents.

## Documentation

- [AGENTS.md](AGENTS.md) — AI agent context and project rules
- [docs/INDEX.md](docs/INDEX.md) — Full documentation index

## License

MIT

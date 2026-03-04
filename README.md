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
│  (OCR → Chunk →     │
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

Models: Azure AI Foundry (via LiteLLM)
```

## Tech Stack

| Layer | Technology |
|---|---|
| RAG Framework | LlamaIndex |
| Agent Framework | LangGraph |
| Vector Store | Pinecone |
| LLM / Embeddings | Azure AI Foundry (OpenAI models) |
| LLM Proxy | LiteLLM |
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
│   └── chat.py                # Interactive agent CLI
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
```

### Usage

```bash
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

## Synthetic Agreements

The project includes a generator for 5 synthetic contracts used as demo data:

| # | Agreement | Language | Key Features |
|---|-----------|----------|--------------|
| 1 | IT Service Agreement | EN | Pricing table annex |
| 2 | Mutual NDA | EN | Confidentiality clauses |
| 3 | Office Lease Agreement | PL | Asset inventory annex |
| 4 | Cloud SLA | EN | Metrics + penalty tables |
| 5 | Employment Contract | PL | Compensation table |

PDFs are generated with `fpdf2` (DejaVu Sans for Unicode/Polish support), then degraded with Pillow to simulate scanned documents (rotation, noise, reduced contrast).

## Documentation

- [AGENTS.md](AGENTS.md) — AI agent context and project rules
- [docs/INDEX.md](docs/INDEX.md) — Full documentation index

## License

MIT

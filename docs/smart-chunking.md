# Smart Chunking & Metadata-First Retrieval

## Overview

The ingestion pipeline uses a custom **ContractNodeParser** that understands contract document structure. Instead of splitting text at arbitrary token boundaries, it:

1. Detects section headings (numbered sections, annexes, amendments, Polish legal markers)
2. Splits at section boundaries, preserving clause context
3. Enriches each chunk with structural metadata for precision retrieval

## Section Detection

The parser recognizes these heading patterns:

| Pattern | Examples |
|---------|----------|
| Numbered sections | `1. Scope of Services`, `3. Czynsz i oplaty` |
| Markdown headings | `## 1. Scope of Services`, `# AMENDMENT NO. 2` |
| Annexes | `ANNEX A - Pricing Schedule`, `ZALACZNIK NR 1 - Wykaz` |
| Amendments | `AMENDMENT NO. 1`, `ANEKS NR 1` |
| Polish legal | `§ 1.`, `Rozdział I`, `Artykuł 5` |

Markdown headings (`#`, `##`, `###`) are supported because Azure Document Intelligence OCR returns text in markdown format. The parser also strips Azure DI page header comments (`<!-- PageHeader="..." -->`) before splitting.

## Metadata Fields

Each chunk carries these structural metadata fields (in addition to `contract_id`, `source_type`, `language`, `version`, `effective_date`):

| Field | Type | Description |
|-------|------|-------------|
| `section_type` | string | Controlled vocabulary — see below |
| `section_name` | string | Raw heading text (e.g. "3. Payment Terms") |
| `has_table` | string | `"true"` or `"false"` — detects pipe tables, tab-separated columns, OCR'd table headers, and HTML `<table>` from Azure DI |
| `clause_number` | string | First clause number in chunk (e.g. "3.1") or empty |

### Section Type Vocabulary

| Type | EN Keywords | PL Keywords |
|------|-------------|-------------|
| `scope` | scope, services | przedmiot, zakres |
| `payment` | payment, pricing, rate, fee | czynsz, wynagrodzenie, oplat |
| `termination` | termination | wypowiedzenie, rozwiazanie, czas trwania |
| `confidentiality` | confidentiality, nda | poufnosc, tajemnic |
| `liability` | liability, limitation | odpowiedzialnosc |
| `sla` | service level, uptime, availability, incident | — |
| `penalties` | penalty, credit, breach | kara, sankcj |
| `annex` | annex, schedule, appendix | zalacznik, wykaz |
| `general` | (fallback) | (fallback) |

## Retrieval Filters

The query engine and agent tool support filtering by structural metadata:

```python
# Find payment terms for a specific contract
query_contracts(settings, "hourly rates", contract_id="ITSVC-001", section_type="payment")

# Find all chunks containing tables
query_contracts(settings, "pricing schedule", has_table=True)

# Find a specific clause
query_contracts(settings, "termination notice period", clause_number="2.2")
```

The agent tool exposes these as optional parameters, so the LLM can decide when to apply filters based on the user's question.

## Architecture

```
PDF pages (Azure DI OCR / SimpleDirectoryReader fallback)
    │
    ▼
Filename metadata (parse_filename_metadata)
    │
    ▼
ContractNodeParser
    ├── Split at section boundaries
    ├── Classify section_type
    ├── Detect tables (has_table)
    ├── Extract clause_number
    └── SentenceSplitter fallback for large sections
    │
    ▼
Pinecone (vectors + all metadata)
    │
    ▼
Query Engine (metadata filters + semantic search)
```

## Implementation

- Parser: `src/contract_lens/ingestion/node_parser.py`
- Pipeline integration: `src/contract_lens/ingestion/pipeline.py`
- Retrieval filters: `src/contract_lens/retrieval/query_engine.py`
- Agent tool: `src/contract_lens/agent/tools.py`
- Demo notebook: `notebooks/04_smart_chunking_demo.ipynb`

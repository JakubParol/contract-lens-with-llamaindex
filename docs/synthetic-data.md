# Synthetic Agreement Data

Strategy for generating realistic test agreements with amendments to validate amendment-aware RAG.

## Why Synthetic Data

- Real client agreements are confidential
- We need controlled, reproducible test data
- Allows testing both EN and PL language handling
- Can include edge cases: tables, annexes, multi-page documents
- **Amendments allow testing temporal override logic** — the system must return the latest effective terms

## Contracts and Amendments

| Contract ID | Type | Language | Version | Effective Date | Key Changes |
|---|---|---|---|---|---|
| ITSVC-001 | IT Service Agreement | EN | v1 (base) | 2025-01-15 | Pricing table, 3 consultants, monthly invoicing |
| ITSVC-001 | IT Service Agreement | EN | v2 (amend.) | 2025-07-01 | Rates +15%, team expanded to 5 consultants |
| ITSVC-001 | IT Service Agreement | EN | v3 (amend.) | 2026-01-01 | Rates +10%, new AI/ML tier, bi-weekly invoicing |
| NDA-001 | Mutual NDA | EN | v1 (base) | 2025-03-01 | Confidentiality clauses, 2-year term |
| LEASE-001 | Office Lease | PL | v1 (base) | 2025-02-10 | 25,000 PLN rent, asset inventory |
| LEASE-001 | Office Lease | PL | v2 (amend.) | 2025-09-01 | Rent → 28,500 PLN, 5 parking spaces added |
| SLA-001 | Cloud SLA | EN | v1 (base) | 2025-04-01 | 99.99% uptime, P1 response 15 min |
| SLA-001 | Cloud SLA | EN | v2 (amend.) | 2025-10-01 | Platinum Plus tier, P1 response → 5 min, credit cap → 50% |
| EMP-001 | Employment Contract | PL | v1 (base) | 2025-05-01 | 22,000 PLN salary, benefits table |

## Filename Convention

Each filename encodes metadata for automatic detection during ingestion:

```
{nn}_{contract_id}_{source_type}_{lang}_v{version}_{effective_date}.pdf
```

| Field | Values | Example |
|-------|--------|---------|
| `nn` | Sequential number (01-09) | `01` |
| `contract_id` | Unique ID (e.g., ITSVC-001) | `ITSVC-001` |
| `source_type` | `base` or `amendment` | `amendment` |
| `lang` | `en` or `pl` | `en` |
| `version` | `v1`, `v2`, `v3` | `v2` |
| `effective_date` | ISO date | `2025-07-01` |

Example: `02_ITSVC-001_amendment_en_v2_2025-07-01.pdf`

## Generation Pipeline

### Step 1: Generate clean PDFs (`scripts/generate_agreements.py`)

Uses `fpdf2` with DejaVu Sans font (Unicode support) to create:
- Base contracts with full clauses, tables, annexes, signature blocks
- Amendments that explicitly reference the base contract and override specific clauses
- Each document includes Contract ID, Effective Date, and Version in the header

Output: `data/agreements/*.pdf` (9 files: 5 bases + 4 amendments)

### Step 2: Simulate scans (`scripts/simulate_scans.py`)

Uses `pdf2image` + `Pillow` to degrade PDF quality:
- Convert each page to image (200 DPI)
- Apply slight rotation (±1.5°)
- Add Gaussian noise
- Reduce contrast
- Subtle blur
- Re-assemble as PDF

Output: `data/scans/*.pdf`

## Test Scenarios for Amendment-Aware RAG

| # | Query | Expected Behavior |
|---|-------|-------------------|
| 1 | "What is the hourly rate for a Senior Architect?" | Return $310 (from v3, 2026-01-01), not $250 (base) |
| 2 | "What is the monthly rent for the office?" | Return 28,500 PLN (from amendment), not 25,000 PLN (base) |
| 3 | "What is the P1 incident response time?" | Return 5 minutes (from amendment), not 15 minutes (base) |
| 4 | "Show the history of rate changes in ITSVC-001" | List all 3 versions chronologically |
| 5 | "What changed in the latest lease amendment?" | Rent increase, parking spaces, deposit adjustment |
| 6 | "What are the NDA confidentiality obligations?" | Return from base (no amendments exist) |

## Navigation

- [INDEX.md](INDEX.md)
- [README.md](../README.md)

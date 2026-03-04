# Synthetic Agreement Data

Strategy for generating realistic test agreements to validate the RAG pipeline.

## Why Synthetic Data

- Real client agreements are confidential
- We need controlled, reproducible test data
- Allows testing both EN and PL language handling
- Can include edge cases: tables, annexes, multi-page documents

## Agreements to Generate

| # | Type | Language | Pages | Annexes | Key Features |
|---|---|---|---|---|---|
| 1 | IT Service Agreement | EN | 4-5 | Pricing table | Service scope, SLA references, payment terms |
| 2 | Mutual NDA | EN | 2-3 | None | Confidentiality clauses, term/termination |
| 3 | Office Lease Agreement | PL | 5-6 | Asset inventory list | Rental terms, deposit, maintenance obligations |
| 4 | Cloud SLA Agreement | EN | 3-4 | Metrics table | Uptime guarantees, penalty matrix, escalation |
| 5 | Employment Contract | PL | 3-4 | Compensation table | Salary, benefits, non-compete, notice period |

## Generation Pipeline

### Step 1: Generate clean PDFs (`scripts/generate_agreements.py`)

Uses `fpdf2` to programmatically create PDFs:
- Realistic headers (company names, addresses, dates)
- Numbered clauses and sub-clauses
- Tables (pricing, metrics, asset lists)
- Signature blocks
- Page numbers

Output: `data/agreements/*.pdf`

### Step 2: Simulate scans (`scripts/simulate_scans.py`)

Uses `Pillow` to degrade PDF quality to mimic scanned documents:
- Convert each page to image (200-300 DPI)
- Apply slight rotation (random +-1-2 degrees)
- Add Gaussian noise
- Reduce contrast slightly
- Optionally add minor artifacts (spots, shadows)
- Re-assemble as PDF

Output: `data/scans/*.pdf`

## What to Test With This Data

- **OCR accuracy**: Can LlamaIndex correctly extract text from degraded scans?
- **Table extraction**: Are pricing/metrics tables parsed and chunked correctly?
- **Multilingual retrieval**: Does the pipeline handle EN and PL queries appropriately?
- **Cross-document queries**: "Which agreements mention penalties?" (should find SLA + Lease)
- **Annex awareness**: Can the agent reference annex data when answering about the main agreement?

## Navigation

- [INDEX.md](INDEX.md)
- [README.md](../README.md)

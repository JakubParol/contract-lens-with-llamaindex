"""Structure-aware node parser for contract documents.

Detects section boundaries, clauses, and tables in OCR'd contract text,
producing chunks that preserve document structure and carry rich metadata
(section_type, section_name, has_table, clause_number).
"""

from __future__ import annotations

import re
from typing import Any, Sequence

from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import BaseNode, Document, TextNode

# ---------------------------------------------------------------------------
# Section heading detection
# ---------------------------------------------------------------------------

# Matches numbered headings like "1. Scope of Services" or "3. Czynsz i oplaty"
_NUMBERED_HEADING_RE = re.compile(r"^(\d+)\.\s+([A-Z\u0100-\u017F].+)$", re.MULTILINE)

# Matches special headings: ANNEX, ZALACZNIK, ANEKS, §, Rozdział, Artykuł, AMENDMENT
_SPECIAL_HEADING_RE = re.compile(
    r"^(§\s*\d+\.?|Rozdzia[lł]\s+\w+|Artyku[lł]\s+\w+|ANNEX\s+\w+|ZALA[CĆ]ZNIK\s+(?:NR\s+)?\d+|ANEKS\s+(?:NR\s+)?\d+|AMENDMENT\s+NO\.\s*\d+)"
    r"[\s.\-—:]*(.*)$",
    re.MULTILINE | re.IGNORECASE,
)

# Matches clause numbers like "1.1", "3.2", "12.3"
_CLAUSE_RE = re.compile(r"^(\d+\.\d+)\s", re.MULTILINE)

# ---------------------------------------------------------------------------
# Section type classification
# ---------------------------------------------------------------------------

# Ordered: annex checked first (annex headings often contain content keywords like "pricing")
SECTION_KEYWORDS: list[tuple[str, list[str]]] = [
    ("annex", ["annex", "zalacznik", "schedule", "appendix", "wykaz"]),
    ("scope", ["scope", "services", "service description", "przedmiot", "zakres"]),
    ("payment", ["payment", "pricing", "rate", "fee", "czynsz", "wynagrodzenie", "oplat", "cen"]),
    ("termination", ["termination", "term and termination", "wypowiedzenie", "rozwiazanie", "czas trwania"]),
    ("confidentiality", ["confidentiality", "nda", "non-disclosure", "poufnosc", "tajemnic"]),
    ("liability", ["liability", "limitation", "odpowiedzialnosc"]),
    ("sla", ["service level", "uptime", "availability", "sla", "incident", "response time"]),
    ("penalties", ["penalty", "credit", "breach", "kara", "sankcj"]),
]


def classify_section(heading: str) -> str:
    """Map a section heading to a controlled vocabulary type."""
    lower = heading.lower()
    for section_type, keywords in SECTION_KEYWORDS:
        if any(kw in lower for kw in keywords):
            return section_type
    return "general"


# ---------------------------------------------------------------------------
# Table detection
# ---------------------------------------------------------------------------

# Heuristic: lines with multiple pipe chars or tab-separated columns
_TABLE_LINE_RE = re.compile(r"(?:\|.*\|)|(?:\S+\t\S+\t\S+)")

# Also detect common table header patterns from OCR'd fpdf2 output
_TABLE_HEADER_RE = re.compile(
    r"(?:Rate|Amount|Price|Kwota|Ilosc|Lp\.|Priority|Service Tier|Service Category|Skladnik)"
    r".*(?:Rate|Amount|Price|Kwota|Ilosc|Lp\.|Priority|Service Tier|Monthly|Czestotliwosc)",
    re.IGNORECASE,
)


def detect_table(text: str) -> bool:
    """Return True if the text likely contains a table."""
    table_lines = _TABLE_LINE_RE.findall(text)
    if len(table_lines) >= 2:
        return True
    if _TABLE_HEADER_RE.search(text):
        return True
    return False


# ---------------------------------------------------------------------------
# Section splitting
# ---------------------------------------------------------------------------

def _split_into_sections(text: str) -> list[dict[str, str]]:
    """Split document text into sections based on heading patterns.

    Returns a list of dicts with keys: heading, body, heading_number.
    """
    # Find all heading positions
    headings: list[tuple[int, int, str, str]] = []  # (start, end, number, heading_text)

    for m in _NUMBERED_HEADING_RE.finditer(text):
        headings.append((m.start(), m.end(), m.group(1), m.group(0).strip()))

    for m in _SPECIAL_HEADING_RE.finditer(text):
        headings.append((m.start(), m.end(), "", m.group(0).strip()))

    # Sort by position and deduplicate overlapping matches
    headings.sort(key=lambda x: x[0])
    deduped: list[tuple[int, int, str, str]] = []
    for h in headings:
        if deduped and h[0] < deduped[-1][1]:
            continue  # skip overlapping
        deduped.append(h)
    headings = deduped

    if not headings:
        return [{"heading": "", "body": text, "heading_number": ""}]

    sections = []

    # Text before first heading (preamble)
    if headings[0][0] > 0:
        preamble = text[: headings[0][0]].strip()
        if preamble:
            sections.append({"heading": "", "body": preamble, "heading_number": ""})

    # Each heading to the next
    for i, (start, end, number, heading_text) in enumerate(headings):
        next_start = headings[i + 1][0] if i + 1 < len(headings) else len(text)
        body = text[end:next_start].strip()
        sections.append({
            "heading": heading_text,
            "body": f"{heading_text}\n{body}" if body else heading_text,
            "heading_number": number,
        })

    return sections


# ---------------------------------------------------------------------------
# ContractNodeParser
# ---------------------------------------------------------------------------

class ContractNodeParser:
    """Structure-aware node parser for contract documents.

    Splits documents at section boundaries, enriches each chunk with
    structural metadata, and falls back to SentenceSplitter for sections
    that exceed ``chunk_size``.
    """

    def __init__(self, chunk_size: int = 1024, chunk_overlap: int = 128):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._sentence_splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def get_nodes_from_documents(
        self,
        documents: Sequence[Document],
        **kwargs: Any,
    ) -> list[BaseNode]:
        """Parse documents into structure-aware nodes with metadata."""
        all_nodes: list[BaseNode] = []

        for doc in documents:
            doc_metadata = dict(doc.metadata)
            text = doc.get_content()
            sections = _split_into_sections(text)

            for section in sections:
                heading = section["heading"]
                body = section["body"]
                section_type = classify_section(heading) if heading else "general"
                has_table = detect_table(body)

                # Extract first clause number
                clause_match = _CLAUSE_RE.search(body)
                clause_number = clause_match.group(1) if clause_match else ""

                # Build metadata for this section's nodes
                section_meta = {
                    **doc_metadata,
                    "section_type": section_type,
                    "section_name": heading,
                    "has_table": "true" if has_table else "false",
                    "clause_number": clause_number,
                }

                # If section fits in one chunk, create a single node
                if len(body) <= self.chunk_size:
                    node = TextNode(text=body, metadata=section_meta)
                    all_nodes.append(node)
                else:
                    # Fall back to sentence splitting for large sections
                    sub_doc = Document(text=body, metadata=section_meta)
                    sub_nodes = self._sentence_splitter.get_nodes_from_documents([sub_doc])
                    # Preserve section metadata on sub-nodes
                    for node in sub_nodes:
                        node.metadata.update(section_meta)
                    all_nodes.append(node) if not sub_nodes else all_nodes.extend(sub_nodes)

        return all_nodes

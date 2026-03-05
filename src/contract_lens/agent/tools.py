"""RAG tools for the LangGraph agent, wrapping LlamaIndex query engine."""

from __future__ import annotations

from langchain_core.tools import tool

from contract_lens.config import Settings
from contract_lens.retrieval.query_engine import query_contracts
from contract_lens.retrieval.catalog import summarize_document_catalog

# Module-level settings reference, set during graph initialization
_settings: Settings | None = None


def init_tools(settings: Settings) -> None:
    """Initialize tools with application settings. Call before using the agent."""
    global _settings
    _settings = settings


@tool
def search_contracts(
    query: str,
    language: str = "",
    contract_id: str = "",
    source_type: str = "",
    document_type: str = "",
    section_type: str = "",
    has_table: str = "",
    clause_number: str = "",
) -> str:
    """Search the contract knowledge base for information about agreements.

    Use this tool when the user asks about contract terms, clauses, pricing,
    obligations, parties, or any content from the indexed agreements.

    The knowledge base contains base contracts and their amendments. Amendments
    override specific clauses from the base contract. The system automatically
    prioritizes the latest version when terms conflict.

    Args:
        query: The search query describing what information to find.
        language: Optional filter - "en" for English, "pl" for Polish. Leave empty for all.
        contract_id: Optional filter - contract ID like "ITSVC-001", "SLA-001". Leave empty for all.
        source_type: Optional filter - "base" for original contracts, "amendment" for amendments only. Leave empty for all.
        document_type: Optional filter - "contract" for base contracts, "amendment" for amendments. Leave empty for all.
        section_type: Optional filter by section type. Values: "scope", "payment", "termination",
            "confidentiality", "liability", "sla", "penalties", "annex", "general". Leave empty for all.
        has_table: Optional filter - "true" to find only chunks with tables, "false" for chunks without. Leave empty for all.
        clause_number: Optional filter - specific clause like "3.1", "4.2". Leave empty for all.
    """
    if _settings is None:
        return "Error: tools not initialized. Call init_tools() first."

    # Convert has_table string to bool or None
    has_table_bool: bool | None = None
    if has_table.lower() == "true":
        has_table_bool = True
    elif has_table.lower() == "false":
        has_table_bool = False

    return query_contracts(
        _settings,
        question=query,
        language=language or None,
        contract_id=contract_id or None,
        source_type=source_type or None,
        document_type=document_type or None,
        section_type=section_type or None,
        has_table=has_table_bool,
        clause_number=clause_number or None,
    )


@tool
def count_contract_documents(
    include_amendments: str = "true",
) -> str:
    """Count indexed contract documents using metadata (document-level, not chunk-level).

    Use this tool for questions like:
    - "How many contracts do we have?"
    - "How many amendments are indexed?"
    - "How many Polish contracts do we have?"

    Args:
        include_amendments: "true" to include amendments in totals, "false" for base contracts only.
    """
    if _settings is None:
        return "Error: tools not initialized. Call init_tools() first."

    summary = summarize_document_catalog(_settings)
    by_language = summary.get("by_language", {})

    include_amend = include_amendments.strip().lower() != "false"

    if include_amend:
        lang_parts = [
            f"{lang_key}(docs={stats['documents']},contracts={stats['contracts']},amendments={stats['amendments']})"
            for lang_key, stats in sorted(by_language.items())
        ]
        lang_summary = ", ".join(lang_parts) if lang_parts else "none"
        return (
            f"Total documents={summary['total_documents']}, contracts={summary['contracts']}, "
            f"amendments={summary['amendments']}, unique_contract_ids={summary['unique_contract_ids']}. "
            f"By language: {lang_summary}."
        )

    lang_contract_parts = [
        f"{lang_key}(contracts={stats['contracts']})"
        for lang_key, stats in sorted(by_language.items())
    ]
    lang_contract_summary = ", ".join(lang_contract_parts) if lang_contract_parts else "none"
    return (
        f"Contracts={summary['contracts']} (base contracts only), "
        f"unique_contract_ids={summary['unique_contract_ids']}. "
        f"By language: {lang_contract_summary}."
    )

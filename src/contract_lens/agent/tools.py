"""RAG tools for the LangGraph agent, wrapping LlamaIndex query engine."""

from __future__ import annotations

from langchain_core.tools import tool

from contract_lens.config import Settings
from contract_lens.retrieval.query_engine import query_contracts

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
    """
    if _settings is None:
        return "Error: tools not initialized. Call init_tools() first."
    return query_contracts(
        _settings,
        question=query,
        language=language or None,
        contract_id=contract_id or None,
        source_type=source_type or None,
    )

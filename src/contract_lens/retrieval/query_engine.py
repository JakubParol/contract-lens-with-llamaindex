"""LlamaIndex query engine over Pinecone vector store with amendment awareness."""

from __future__ import annotations

from llama_index.core import VectorStoreIndex
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.vector_stores import MetadataFilters, MetadataFilter, FilterOperator

from contract_lens.config import Settings
from contract_lens.ingestion.pipeline import (
    build_embedding_model,
    build_llm,
    build_pinecone_vector_store,
)
from contract_lens.retrieval.amendment_retriever import AmendmentAwareRetriever

AMENDMENT_AWARE_PROMPT = (
    "You are a contract analysis assistant. The knowledge base contains base contracts "
    "and their amendments (aneksy). Amendments override specific clauses from the base contract.\n\n"
    "IMPORTANT RULES:\n"
    "- Each document has metadata: contract_id, source_type (base/amendment), document_type (contract/amendment), "
    "language (en/pl), version, effective_date.\n"
    "- Chunks also carry structural metadata: section_type (scope, payment, termination, confidentiality, "
    "liability, sla, penalties, annex, general), section_name, has_table, clause_number.\n"
    "- Questions about counts (e.g., number of contracts/amendments) should distinguish base contracts from amendments.\n"
    "- For count questions without an explicit language constraint, count across ALL languages.\n"
    "- When terms conflict between a base contract and an amendment, ALWAYS use the amendment's terms "
    "(the one with the higher version number or later effective_date).\n"
    "- When asked about current terms (rates, prices, SLA targets, etc.), return the LATEST version.\n"
    "- When asked about history or changes, list all versions chronologically.\n"
    "- Always mention which version/date your answer comes from.\n"
)


def build_query_engine(
    settings: Settings,
    language: str | None = None,
    contract_id: str | None = None,
    source_type: str | None = None,
    document_type: str | None = None,
    section_type: str | None = None,
    has_table: bool | None = None,
    clause_number: str | None = None,
    similarity_top_k: int = 8,
):
    """Build a LlamaIndex query engine over the Pinecone index.

    Args:
        settings: Application settings.
        language: Filter by language ("en" or "pl"). None = all.
        contract_id: Filter by contract ID (e.g., "ITSVC-001"). None = all.
        source_type: Filter by source type ("base" or "amendment"). None = all.
        document_type: Filter by document type ("contract" or "amendment"). None = all.
        section_type: Filter by section type (scope, payment, termination,
            confidentiality, liability, sla, penalties, annex, general). None = all.
        has_table: Filter for chunks containing tables. None = all.
        clause_number: Filter by clause number (e.g., "3.1"). None = all.
        similarity_top_k: Number of similar chunks to retrieve.
    """
    vector_store = build_pinecone_vector_store(settings)
    embed_model = build_embedding_model(settings)
    llm = build_llm(settings)

    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embed_model,
    )

    # Build metadata filters if specified
    filter_list = []
    if language:
        filter_list.append(MetadataFilter(key="language", value=language, operator=FilterOperator.EQ))
    if contract_id:
        filter_list.append(MetadataFilter(key="contract_id", value=contract_id.upper(), operator=FilterOperator.EQ))
    if source_type:
        filter_list.append(MetadataFilter(key="source_type", value=source_type.lower(), operator=FilterOperator.EQ))
    if document_type:
        filter_list.append(MetadataFilter(key="document_type", value=document_type.lower(), operator=FilterOperator.EQ))
    if section_type:
        filter_list.append(MetadataFilter(key="section_type", value=section_type.lower(), operator=FilterOperator.EQ))
    if has_table is not None:
        filter_list.append(MetadataFilter(key="has_table", value="true" if has_table else "false", operator=FilterOperator.EQ))
    if clause_number:
        filter_list.append(MetadataFilter(key="clause_number", value=clause_number, operator=FilterOperator.EQ))

    filters = MetadataFilters(filters=filter_list) if filter_list else None

    retriever = AmendmentAwareRetriever(
        index=index,
        top_k=similarity_top_k,
        filters=filters,
    )

    synthesizer = get_response_synthesizer(
        llm=llm,
        response_mode="compact",
    )

    return RetrieverQueryEngine.from_args(
        retriever=retriever,
        response_synthesizer=synthesizer,
        system_prompt=AMENDMENT_AWARE_PROMPT,
    )


def query_contracts(
    settings: Settings,
    question: str,
    language: str | None = None,
    contract_id: str | None = None,
    source_type: str | None = None,
    document_type: str | None = None,
    section_type: str | None = None,
    has_table: bool | None = None,
    clause_number: str | None = None,
) -> str:
    """Query the contract knowledge base and return a synthesized answer.

    The query engine is amendment-aware: it prioritizes the latest version
    of any clause when terms conflict between base contracts and amendments.
    """
    engine = build_query_engine(
        settings,
        language=language,
        contract_id=contract_id,
        source_type=source_type,
        document_type=document_type,
        section_type=section_type,
        has_table=has_table,
        clause_number=clause_number,
    )
    response = engine.query(question)
    return str(response)

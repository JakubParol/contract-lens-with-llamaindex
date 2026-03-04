"""LlamaIndex query engine over Pinecone vector store."""

from __future__ import annotations

from llama_index.core import VectorStoreIndex
from llama_index.core.vector_stores import MetadataFilters, MetadataFilter, FilterOperator

from contract_lens.config import Settings
from contract_lens.ingestion.pipeline import (
    build_embedding_model,
    build_llm,
    build_pinecone_vector_store,
)


def build_query_engine(
    settings: Settings,
    language: str | None = None,
    document_type: str | None = None,
    similarity_top_k: int = 5,
):
    """Build a LlamaIndex query engine over the Pinecone index.

    Args:
        settings: Application settings.
        language: Filter by language ("en" or "pl"). None = all.
        document_type: Filter by type ("agreement" or "annex"). None = all.
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
    filters = None
    filter_list = []
    if language:
        filter_list.append(MetadataFilter(key="language", value=language, operator=FilterOperator.EQ))
    if document_type:
        filter_list.append(MetadataFilter(key="document_type", value=document_type, operator=FilterOperator.EQ))
    if filter_list:
        filters = MetadataFilters(filters=filter_list)

    return index.as_query_engine(
        llm=llm,
        similarity_top_k=similarity_top_k,
        filters=filters,
    )


def query_contracts(
    settings: Settings,
    question: str,
    language: str | None = None,
    document_type: str | None = None,
) -> str:
    """Query the contract knowledge base and return a synthesized answer."""
    engine = build_query_engine(settings, language=language, document_type=document_type)
    response = engine.query(question)
    return str(response)

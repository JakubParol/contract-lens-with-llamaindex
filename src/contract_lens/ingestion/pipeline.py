"""LlamaIndex ingestion pipeline: load scanned PDFs, chunk, embed, upsert to Pinecone."""

from __future__ import annotations

import re
from pathlib import Path

from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.vector_stores.pinecone import PineconeVectorStore
from pinecone import Pinecone

from contract_lens.config import Settings
from contract_lens.ingestion.node_parser import ContractNodeParser

# Filename pattern: {nn}_{contract_id}_{source_type}_{lang}_v{version}_{effective_date}.pdf
_FILENAME_RE = re.compile(
    r"^\d+_(?P<contract_id>[A-Z]+-\d+)_(?P<source_type>base|amendment)_(?P<lang>en|pl)_v(?P<version>\d+)_(?P<effective_date>\d{4}-\d{2}-\d{2})\.pdf$",
    re.IGNORECASE,
)


def parse_filename_metadata(filename: str) -> dict[str, str]:
    """Extract amendment-aware metadata from filename convention.

    Expected format: {nn}_{contract_id}_{source_type}_{lang}_v{version}_{effective_date}.pdf
    Example: 02_ITSVC-001_amendment_en_v2_2025-07-01.pdf

    Returns dict with: contract_id, source_type, language, version, effective_date.
    Falls back to basic detection if filename doesn't match the convention.
    """
    match = _FILENAME_RE.match(filename)
    if match:
        return {
            "contract_id": match.group("contract_id").upper(),
            "source_type": match.group("source_type").lower(),
            "language": match.group("lang").lower(),
            "version": match.group("version"),
            "effective_date": match.group("effective_date"),
        }

    # Fallback for files not matching the convention
    lower = filename.lower()
    return {
        "contract_id": "UNKNOWN",
        "source_type": "base",
        "language": "pl" if "_pl" in lower else "en",
        "version": "1",
        "effective_date": "",
    }


def build_embedding_model(settings: Settings) -> AzureOpenAIEmbedding:
    return AzureOpenAIEmbedding(
        deployment_name=settings.azure_openai_embedding_deployment,
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )


def build_llm(settings: Settings) -> AzureOpenAI:
    return AzureOpenAI(
        deployment_name=settings.azure_openai_deployment,
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )


def build_pinecone_vector_store(settings: Settings) -> PineconeVectorStore:
    pc = Pinecone(api_key=settings.pinecone_api_key)
    index = pc.Index(settings.pinecone_index_name)
    return PineconeVectorStore(pinecone_index=index)


def run_ingestion(
    settings: Settings,
    data_dir: str | Path = "data/scans",
) -> int:
    """Run the full ingestion pipeline.

    Returns the number of nodes ingested.
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_path}")

    # Load documents
    reader = SimpleDirectoryReader(input_dir=str(data_path), recursive=False)
    documents = reader.load_data()

    # Enrich metadata from filename convention
    for doc in documents:
        filename = doc.metadata.get("file_name", "")
        meta = parse_filename_metadata(filename)
        doc.metadata.update(meta)

    # Structure-aware chunking: splits at section boundaries and enriches metadata
    parser = ContractNodeParser(chunk_size=1024, chunk_overlap=128)
    nodes = parser.get_nodes_from_documents(documents)

    # Build components
    embed_model = build_embedding_model(settings)
    vector_store = build_pinecone_vector_store(settings)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Create index (embeds + upserts)
    VectorStoreIndex(
        nodes,
        embed_model=embed_model,
        storage_context=storage_context,
        show_progress=True,
    )

    return len(nodes)

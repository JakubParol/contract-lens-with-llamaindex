"""LlamaIndex ingestion pipeline: load scanned PDFs, chunk, embed, upsert to Pinecone."""

from __future__ import annotations

from pathlib import Path

from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.vector_stores.pinecone import PineconeVectorStore
from pinecone import Pinecone

from contract_lens.config import Settings


def _detect_language(filename: str) -> str:
    """Detect language from filename convention: *_pl.pdf or *_en.pdf."""
    lower = filename.lower()
    if "_pl" in lower:
        return "pl"
    return "en"


def _detect_document_type(filename: str) -> str:
    """Detect document type from filename."""
    lower = filename.lower()
    if "annex" in lower or "zalacznik" in lower:
        return "annex"
    return "agreement"


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

    # Enrich metadata
    for doc in documents:
        filename = doc.metadata.get("file_name", "")
        doc.metadata["language"] = _detect_language(filename)
        doc.metadata["document_type"] = _detect_document_type(filename)

    # Chunk with settings tuned for contracts (larger chunks preserve clause context)
    splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=128)
    nodes = splitter.get_nodes_from_documents(documents)

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

"""Document loading with optional Azure Document Intelligence OCR for scanned PDFs."""

from __future__ import annotations

import base64
import logging
from pathlib import Path

from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import Document

from contract_lens.config import Settings

logger = logging.getLogger(__name__)


def load_documents(settings: Settings, data_dir: Path) -> list[Document]:
    """Load PDFs — with Azure DI OCR if configured, otherwise SimpleDirectoryReader."""
    if settings.azure_doc_intelligence_endpoint and settings.azure_doc_intelligence_key:
        return _load_with_ocr(settings, data_dir)

    logger.info("Azure Document Intelligence not configured, using SimpleDirectoryReader")
    return SimpleDirectoryReader(input_dir=str(data_dir), recursive=False).load_data()


def _load_with_ocr(settings: Settings, data_dir: Path) -> list[Document]:
    """Load PDFs using Azure Document Intelligence OCR (prebuilt-layout model)."""
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
    from azure.core.credentials import AzureKeyCredential

    client = DocumentIntelligenceClient(
        endpoint=settings.azure_doc_intelligence_endpoint,
        credential=AzureKeyCredential(settings.azure_doc_intelligence_key),
    )

    pdf_files = sorted(data_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning("No PDF files found in %s", data_dir)
        return []

    documents: list[Document] = []
    for pdf_path in pdf_files:
        logger.info("OCR processing: %s", pdf_path.name)
        pdf_bytes = pdf_path.read_bytes()

        request = AnalyzeDocumentRequest(
            bytes_source=base64.b64encode(pdf_bytes).decode(),
        )
        poller = client.begin_analyze_document(
            model_id="prebuilt-layout",
            body=request,
            output_content_format="markdown",
        )
        result = poller.result()

        content = result.content or ""
        if not content.strip():
            logger.warning("OCR returned empty text for %s", pdf_path.name)
            continue

        documents.append(
            Document(
                text=content,
                metadata={"file_name": pdf_path.name},
            )
        )

    logger.info("OCR loaded %d documents from %s", len(documents), data_dir)
    return documents

"""CLI entry point to run the ingestion pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path for direct script execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from contract_lens.config import get_settings
from contract_lens.observability import init_observability
from contract_lens.ingestion.pipeline import run_ingestion


def main():
    parser = argparse.ArgumentParser(description="Ingest scanned agreements into Pinecone")
    parser.add_argument(
        "--data-dir",
        default="data/scans",
        help="Directory containing scanned PDF files (default: data/scans)",
    )
    args = parser.parse_args()

    settings = get_settings()
    init_observability(settings)

    print(f"Ingesting documents from: {args.data_dir}")
    node_count = run_ingestion(settings, data_dir=args.data_dir)
    print(f"Ingestion complete: {node_count} nodes indexed in Pinecone")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Terminal menu launcher for Contract Lens POC workflows and maintenance."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _line() -> None:
    print("-" * 60)


def _title(text: str) -> None:
    print()
    _line()
    print(text)
    _line()


def run_command(label: str, cmd: list[str]) -> bool:
    _title(f"Running: {label}")
    print(" ".join(cmd))
    print()
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    if result.returncode != 0:
        print(f"\nCommand failed ({result.returncode}): {label}")
        return False
    print(f"\nDone: {label}")
    return True


def confirm_yes(prompt: str = "Type 'yes' to continue: ") -> bool:
    return input(prompt).strip().lower() == "yes"


def confirm_reset_token() -> bool:
    return input("Type 'RESET' to confirm full reset: ").strip() == "RESET"


def delete_pdf_files(directory: Path) -> None:
    if not directory.exists():
        print(f"Directory not found: {directory}")
        return

    pdfs = sorted(directory.glob("*.pdf"))
    if not pdfs:
        print(f"No PDF files found in {directory}")
        return

    for path in pdfs:
        path.unlink()

    print(f"Deleted {len(pdfs)} files from {directory}")


def show_data_dir_status() -> None:
    _title("Data Directories Status")
    for rel_path in ("data/agreements", "data/scans"):
        path = REPO_ROOT / rel_path
        pdf_count = len(list(path.glob("*.pdf"))) if path.exists() else 0
        print(f"{rel_path}: {pdf_count} PDFs")


def action_generate_agreements() -> bool:
    return run_command(
        "Generate agreements",
        [sys.executable, str(REPO_ROOT / "scripts" / "generate_agreements.py")],
    )


def action_simulate_scans() -> bool:
    return run_command(
        "Simulate scans",
        [sys.executable, str(REPO_ROOT / "scripts" / "simulate_scans.py")],
    )


def action_ingest() -> bool:
    return run_command(
        "Ingest vectors",
        [sys.executable, str(REPO_ROOT / "scripts" / "ingest.py")],
    )


def action_chat() -> bool:
    return run_command(
        "Chat agent",
        [sys.executable, str(REPO_ROOT / "scripts" / "chat.py")],
    )


def action_reset_vector_db() -> bool:
    if not confirm_yes():
        print("Cancelled.")
        return False
    return run_command(
        "Reset vector DB",
        [str(REPO_ROOT / "scripts" / "reset_vector_db.sh"), "--yes"],
    )


def action_show_vector_stats() -> bool:
    return run_command(
        "Show vector DB stats",
        [str(REPO_ROOT / "scripts" / "show_vector_db_stats.sh")],
    )


def action_delete_agreements() -> bool:
    if not confirm_yes():
        print("Cancelled.")
        return False
    delete_pdf_files(REPO_ROOT / "data" / "agreements")
    return True


def action_delete_scans() -> bool:
    if not confirm_yes():
        print("Cancelled.")
        return False
    delete_pdf_files(REPO_ROOT / "data" / "scans")
    return True


def action_full_reset() -> bool:
    _title("Full Reset")
    print("This will:")
    print("1) Clear all vectors from Pinecone index")
    print("2) Delete all PDFs from data/agreements")
    print("3) Delete all PDFs from data/scans")
    print()
    if not confirm_yes():
        print("Cancelled.")
        return False
    if not confirm_reset_token():
        print("Cancelled.")
        return False

    ok = run_command(
        "Reset vector DB",
        [str(REPO_ROOT / "scripts" / "reset_vector_db.sh"), "--yes"],
    )
    delete_pdf_files(REPO_ROOT / "data" / "agreements")
    delete_pdf_files(REPO_ROOT / "data" / "scans")
    return ok


def quick_workflow() -> None:
    _title("Quick Workflow (E2E)")
    reset_input = input("Reset vector DB before ingest? [Y/n]: ").strip().lower()
    do_reset = reset_input in ("", "y", "yes")

    if do_reset:
        print("Vector DB reset is enabled for this run.")
        if not confirm_yes():
            print("Cancelled.")
            return
        if not run_command(
            "Reset vector DB",
            [str(REPO_ROOT / "scripts" / "reset_vector_db.sh"), "--yes"],
        ):
            return

    if not action_generate_agreements():
        return
    if not action_simulate_scans():
        return
    if not action_ingest():
        return

    print("\nOpening chat. Exit with: quit")
    action_chat()


def step_by_step_menu() -> None:
    while True:
        _title("Workflow Krok po Kroku")
        print("[1] Generate agreements")
        print("[2] Simulate scans")
        print("[3] Ingest vectors")
        print("[4] Open chat")
        print("[0] Back")
        choice = input("\nSelect option: ").strip()

        if choice == "1":
            action_generate_agreements()
        elif choice == "2":
            action_simulate_scans()
        elif choice == "3":
            action_ingest()
        elif choice == "4":
            action_chat()
        elif choice == "0":
            return
        else:
            print("Invalid option.")


def maintenance_menu() -> None:
    while True:
        _title("Maintenance")
        print("[1] Clear vector DB")
        print("[2] Show vector DB status")
        print("[3] Delete agreements (data/agreements)")
        print("[4] Delete scans (data/scans)")
        print("[5] Full reset")
        print("[0] Back")
        choice = input("\nSelect option: ").strip()

        if choice == "1":
            action_reset_vector_db()
        elif choice == "2":
            action_show_vector_stats()
        elif choice == "3":
            action_delete_agreements()
        elif choice == "4":
            action_delete_scans()
        elif choice == "5":
            action_full_reset()
        elif choice == "0":
            return
        else:
            print("Invalid option.")


def diagnostics_menu() -> None:
    while True:
        _title("Diagnostics")
        print("[1] Data directories status")
        print("[0] Back")
        choice = input("\nSelect option: ").strip()

        if choice == "1":
            show_data_dir_status()
        elif choice == "0":
            return
        else:
            print("Invalid option.")


def main() -> int:
    while True:
        _title("Contract Lens TUI")
        print("[1] Quick Workflow (E2E)")
        print("[2] Workflow Krok po Kroku")
        print("[3] Maintenance")
        print("[4] Diagnostics")
        print("[0] Exit")
        choice = input("\nSelect option: ").strip()

        if choice == "1":
            quick_workflow()
        elif choice == "2":
            step_by_step_menu()
        elif choice == "3":
            maintenance_menu()
        elif choice == "4":
            diagnostics_menu()
        elif choice == "0":
            print("Bye.")
            return 0
        else:
            print("Invalid option.")


if __name__ == "__main__":
    raise SystemExit(main())

"""Interactive CLI for the contract analysis agent."""

from __future__ import annotations

import sys
from pathlib import Path

from langchain_core.messages import HumanMessage

# Add src to path for direct script execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from contract_lens.config import get_settings
from contract_lens.observability import init_observability
from contract_lens.agent.graph import build_agent


def main():
    settings = get_settings()
    init_observability(settings)

    print("Contract Lens Agent")
    print("=" * 40)
    print("Ask questions about your contracts. Type 'quit' to exit.\n")

    agent, callback_handler = build_agent(settings)
    config = {"callbacks": [callback_handler]} if callback_handler else {}

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        result = agent.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
        )

        # Print the last AI message
        ai_message = result["messages"][-1]
        print(f"\nAgent: {ai_message.content}\n")


if __name__ == "__main__":
    main()

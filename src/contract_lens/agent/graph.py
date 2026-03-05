"""LangGraph ReAct agent for contract analysis."""

from __future__ import annotations

from langchain_openai import AzureChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from contract_lens.config import Settings
from contract_lens.agent.state import AgentState
from contract_lens.agent.tools import search_contracts, count_contract_documents, init_tools
from contract_lens.observability import get_langfuse_callback_handler


def _build_llm(settings: Settings) -> AzureChatOpenAI:
    return AzureChatOpenAI(
        azure_deployment=settings.azure_openai_deployment,
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )


def _should_continue(state: AgentState) -> str:
    """Route: if the last message has tool calls, go to tools. Otherwise end."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END


def build_agent(settings: Settings):
    """Build and compile the LangGraph agent.

    Returns a compiled graph and optional LangFuse callback handler.
    """
    init_tools(settings)

    tools = [search_contracts, count_contract_documents]
    llm = _build_llm(settings).bind_tools(tools)

    def call_model(state: AgentState) -> dict:
        response = llm.invoke(state["messages"])
        return {"messages": [response]}

    # Build graph
    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(tools))

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", _should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    compiled = graph.compile()

    # Get optional LangFuse handler
    callback_handler = get_langfuse_callback_handler(settings)

    return compiled, callback_handler

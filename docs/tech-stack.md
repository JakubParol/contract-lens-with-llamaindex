# Tech Stack

Decisions and rationale for each technology choice. Last updated: 2026-03-04.

## Core Stack

| Technology | Role | Why |
|---|---|---|
| **Python 3.12** | Runtime | Stable, full ecosystem support. 3.13 has occasional issues with LlamaIndex integrations. |
| **Poetry** | Dependency management | Lockfile, dependency groups (dev/prod), cleaner than pip. |
| **LlamaIndex** | RAG framework | Best-in-class for document ingestion, chunking, OCR, embeddings, and retrieval. Superior to LangChain for document-heavy RAG. |
| **LangGraph** | Agent framework | Minimal, graph-based agent orchestration. Used only for the agent layer, not for RAG. |
| **Pinecone** | Vector database | Managed, serverless, fast. Good for POC — no infra to manage. |
| **Azure AI Foundry** | LLM + Embeddings provider | Client/company standard. Hosts GPT-4 and embedding models. |
| **LangFuse** | Observability | Traces both LlamaIndex and LangChain/LangGraph in one dashboard. Open-source option available. |
| **pydantic-settings** | Configuration | Type-safe config from `.env` files. |

## Why LlamaIndex over LangChain for RAG

LangChain is widely known but for document-processing RAG, LlamaIndex is the better fit:

- **Document connectors**: `SimpleDirectoryReader` handles PDF, DOCX, images out of the box
- **Chunking strategies**: `SentenceSplitter`, `SemanticSplitter`, hierarchical — all first-class
- **Query engines**: Built-in response synthesis, sub-question decomposition, routing
- **Vector store integrations**: Pinecone, Azure AI Search, Qdrant — all with metadata filtering
- **Evaluation**: Built-in relevance and faithfulness evaluation

LangChain is used here **only** via LangGraph for agent orchestration — the two frameworks complement each other.

## Why Both Frameworks

```
LlamaIndex handles:          LangGraph handles:
- Document loading            - Agent state management
- OCR / parsing               - Tool routing (ReAct)
- Chunking                    - Conversation flow
- Embedding                   - Multi-step reasoning
- Vector store ops
- Query + synthesis
```

The boundary is clean: LlamaIndex is wrapped as a **tool** that LangGraph's agent can call.

## Dependency Versions

Pinned in `pyproject.toml`. Key packages:

- `llama-index` — core + integration packages (vector-stores-pinecone, embeddings-azure-openai, llms-azure-openai, readers-file)
- `langgraph` — agent graph
- `langchain-openai` — `AzureChatOpenAI` for LangGraph nodes
- `langfuse` — observability
- `pinecone` — vector DB client (note: `pinecone-client` is deprecated)
- `fpdf2` + `Pillow` — dev dependencies for synthetic data generation

## Navigation

- [INDEX.md](INDEX.md)
- [README.md](../README.md)

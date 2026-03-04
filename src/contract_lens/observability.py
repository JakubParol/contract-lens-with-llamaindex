from contract_lens.config import Settings


def init_observability(settings: Settings) -> None:
    """Initialize LangFuse tracing for LlamaIndex and LangChain/LangGraph.

    Call once at application startup. No-op if LangFuse keys are not configured.
    """
    if not settings.langfuse_enabled:
        return

    import os

    # Langfuse v3 uses OTEL-based instrumentation via openinference
    os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.langfuse_public_key)
    os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.langfuse_secret_key)
    os.environ.setdefault("LANGFUSE_HOST", settings.langfuse_host)

    from openinference.instrumentation.llama_index import LlamaIndexInstrumentor

    LlamaIndexInstrumentor().instrument()


def get_langfuse_callback_handler(settings: Settings):
    """Return a LangFuse callback handler for LangChain/LangGraph.

    Returns None if LangFuse is not configured.
    """
    if not settings.langfuse_enabled:
        return None

    from langfuse.langchain import CallbackHandler

    return CallbackHandler(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )

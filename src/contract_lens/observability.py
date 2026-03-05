import logging

from contract_lens.config import Settings

logger = logging.getLogger(__name__)


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

    try:
        from langfuse.langchain import CallbackHandler
    except ModuleNotFoundError as exc:
        logger.warning(
            "LangFuse callback handler disabled (%s). Install `langchain` to enable LangFuse LangChain integration.",
            exc,
        )
        return None

    # Langfuse v3 callback uses initialized/default client from environment.
    return CallbackHandler()

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter
from typing import Any

from langfuse import Langfuse

from multi_agent_research_lab.core.config import get_settings

logger = logging.getLogger(__name__)

# Global Langfuse instance (optional, can be initialized per span)
_langfuse = None


def get_langfuse() -> Langfuse | None:
    global _langfuse
    if _langfuse is None:
        settings = get_settings()
        if settings.model_dump().get("langfuse_secret_key"):
            _langfuse = Langfuse(
                secret_key=settings.model_dump().get("langfuse_secret_key"),
                public_key=settings.model_dump().get("langfuse_public_key"),
                host=settings.model_dump().get("langfuse_base_url") or "https://cloud.langfuse.com"
            )
    return _langfuse


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Minimal span context integrated with logging and Langfuse."""
    started = perf_counter()
    
    logger.info(f"Starting span: {name} {attributes or ''}")
    
    # Langfuse event
    lf = get_langfuse()
    if lf:
        lf.create_event(name=name, metadata=attributes)

    span: dict[str, Any] = {"name": name, "attributes": attributes or {}, "duration_seconds": None}
    try:
        yield span
    finally:
        duration = perf_counter() - started
        span["duration_seconds"] = duration
        logger.info(f"Finished span: {name} in {duration:.4f}s")

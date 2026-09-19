"""Langfuse + OpenTelemetry observability for the ADK research agent.

Wires the OpenInference Google ADK instrumentor into Langfuse Cloud so that
every agent run, model generation, and tool call becomes a trace with
observations. Import-safe and idempotent.
"""
from __future__ import annotations

import atexit
import os
import sys

from dotenv import load_dotenv

_initialized = False


def setup_observability() -> None:
    """Load credentials, instrument Google ADK, and register a flush at exit.

    Idempotent: calling more than once is a no-op.
    """
    global _initialized
    if _initialized:
        return

    load_dotenv()

    # The Langfuse SDK reads LANGFUSE_HOST; the assignment env var is
    # LANGFUSE_BASE_URL. Bridge the two so either name works without leaking
    # credentials into user code.
    base_url = os.getenv("LANGFUSE_BASE_URL")
    if base_url and not os.getenv("LANGFUSE_HOST"):
        os.environ["LANGFUSE_HOST"] = base_url

    missing = [
        var
        for var in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY")
        if not os.getenv(var)
    ]
    if missing:
        print(
            f"[observability] Missing env vars: {', '.join(missing)}. "
            "Traces will not reach Langfuse.",
            file=sys.stderr,
            flush=True,
        )
        _initialized = True
        return

    from langfuse import get_client
    from openinference.instrumentation.google_adk import GoogleADKInstrumentor

    client = get_client()

    try:
        if not client.auth_check():
            print(
                "[observability] Langfuse auth_check failed. "
                "Verify LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY / LANGFUSE_BASE_URL.",
                file=sys.stderr,
                flush=True,
            )
    except Exception as exc:
        print(f"[observability] Langfuse auth_check raised: {exc}", file=sys.stderr, flush=True)

    GoogleADKInstrumentor().instrument()
    atexit.register(flush_langfuse)

    print(
        f"[observability] Langfuse instrumentation ready "
        f"(host={os.getenv('LANGFUSE_HOST')})",
        file=sys.stderr,
        flush=True,
    )
    _initialized = True


def flush_langfuse() -> None:
    """Flush pending Langfuse events. Call before a short-lived process exits."""
    try:
        from langfuse import get_client

        get_client().flush()
    except Exception as exc:
        print(f"[observability] Langfuse flush failed: {exc}", file=sys.stderr, flush=True)

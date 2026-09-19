"""research_agent package.

Importing this package loads .env and installs the Langfuse + OpenTelemetry
instrumentation once, so both `adk web` and the run_agent CLI emit traces.
"""
from __future__ import annotations

import sys

try:
    from research_agent.observability import setup_observability

    setup_observability()
except Exception as exc:  # pragma: no cover
    print(f"[research_agent] observability setup skipped: {exc}", file=sys.stderr, flush=True)

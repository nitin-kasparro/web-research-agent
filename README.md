# Observable Web Research Agent

A beginner-level agentic application built with **Google ADK 2.x**, **Firecrawl**,
and **Langfuse**. A user asks a research question; the agent searches the web,
scrapes the most relevant pages, and returns a concise cited brief. Every run is
traced end-to-end in Langfuse — search query, selected URLs, scrape results,
model generation, final output, latency, user ID and session ID.

## Requirements

- Python 3.10 or later
- A free [Firecrawl](https://www.firecrawl.dev/) account and API key
- A free [Langfuse Cloud](https://cloud.langfuse.com/) project and key pair
- A Google AI Studio [Gemini API key](https://aistudio.google.com/apikey)

## Setup

### 1. Clone and enter the repo

```bash
git clone <this-repo-url> observer-assignment
cd observer-assignment
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
# Windows (PowerShell / Git Bash)
.\.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file and fill in real values:

```bash
cp .env.example .env
```

Then edit `.env`:

| Variable              | Where to get it                                         | Purpose                                    |
| --------------------- | ------------------------------------------------------- | ------------------------------------------ |
| `GOOGLE_API_KEY`      | https://aistudio.google.com/apikey                      | Powers the Gemini LLM the agent uses.      |
| `FIRECRAWL_API_KEY`   | https://www.firecrawl.dev/ → dashboard → API keys       | Authenticates search / scrape calls.       |
| `LANGFUSE_PUBLIC_KEY` | Langfuse project → *Settings → API Keys*                | Trace identity — safe to commit? No.       |
| `LANGFUSE_SECRET_KEY` | Same page as the public key                             | Authenticates trace uploads.               |
| `LANGFUSE_BASE_URL`   | `https://cloud.langfuse.com` (EU) or `https://us.cloud.langfuse.com` (US) | Which Langfuse region to ship traces to. |

**`.env` is gitignored — never commit real keys.**

## Run the agent

Two ways, both required by the assignment.

### From the ADK web dev UI

```bash
adk web --port 8000 .
```

Then open http://127.0.0.1:8000 and pick `research_agent` from the app dropdown.
Type your research question in the chat box. The ADK UI shows the message
timeline; Langfuse shows the full trace tree.

### From the command line

```bash
python -m research_agent.run_agent
```

The CLI wraps every turn in a Langfuse root span with:

- `trace_name = "research: <question>"`
- `tags = ["google-adk", "firecrawl", "beginner-assignment", "local-dev"]`
- `metadata = {assignment_level, tool_provider, research_topic, app_version}`
- explicit `user_id` and `session_id`

After each turn it prints the trace URL you can paste into
`docs/trace_evidence.md`.

## Run the tests

```bash
pytest tests/ -v
```

All 7 required cases (search success / empty / rate-limit, scrape success /
invalid-URL / timeout+empty, secret-safety scan) run against mocked Firecrawl
responses — no live network or API keys needed.

## Confirm traces in Langfuse

1. Send a message from either interface.
2. Wait ~15–30 seconds (Langfuse batches OpenTelemetry spans).
3. Open your Langfuse project → **Tracing** → newest row on top.
4. Click the `invocation [research_agent]` row to open the tree view.

You should see: `invocation → agent_run → call_llm (Gemini) → search_web →
scrape_web_page × N → call_llm (final brief)`.

### Troubleshooting missing traces

| Symptom | Cause | Fix |
| --- | --- | --- |
| ADK web log shows `[observability] Missing env vars: LANGFUSE_...` | `.env` not loaded or keys missing | Confirm `.env` at repo root and restart `adk web` |
| Log shows `[observability] Langfuse auth_check failed` | Wrong keys or wrong `LANGFUSE_BASE_URL` region | Double-check the project's API-Keys page; note EU vs US host |
| Log shows `observability setup skipped: cannot import name 'propagate_attributes'` | Corrupted `langfuse` install in the venv (Windows partial write) | `pip install --force-reinstall --no-deps langfuse==4.15.4` |
| Sent a message, no trace after 60s | Batch flush hasn't fired | Wait a bit longer, then refresh the Langfuse traces list |
| Model call errors `404 gemini-2.5-flash no longer available` | Google deprecated that alias for new keys | Update `model=` in `research_agent/agent.py` (e.g. `gemini-3.6-flash`) |

## Project layout

```
research_agent/
    __init__.py             # runs setup_observability() on import
    agent.py                # root_agent: model, instruction, tools
    firecrawl_tools.py      # search_web and scrape_web_page tools
    observability.py        # Langfuse + OpenTelemetry setup, atexit flush
    run_agent.py            # CLI runner: Runner + InMemorySessionService
docs/
    reading_notes.md        # per-page notes on ADK / Firecrawl / Langfuse docs
    trace_evidence.md       # S1–S6 evidence with screenshots
    screenshots/            # PNGs of Langfuse trace trees
tests/
    test_firecrawl_tools.py # 7 mocked pytest cases
    fixtures/firecrawl_responses.json
.env.example                # placeholder env vars (real .env is gitignored)
requirements.txt            # pinned versions
```

## Architecture in one paragraph

`root_agent` (in `research_agent/agent.py`) is a Google ADK `Agent` with two
Python tools — `search_web` and `scrape_web_page` — that wrap the Firecrawl
SDK. On import, `research_agent/__init__.py` calls
`setup_observability()`, which loads `.env`, verifies Langfuse credentials, and
installs `GoogleADKInstrumentor` so every ADK primitive (agent step, LLM
generation, tool call) automatically becomes an OpenInference span exported to
Langfuse. The CLI runner `run_agent.py` additionally wraps each user turn in
`langfuse.propagate_attributes(...)` so the trace carries a meaningful name,
tags, user_id, session_id, and metadata — exactly what the assignment's
"Instrumentation requirements" section calls for.

## Development notes

AI-assisted work performed with Claude in this repo:

- Bootstrapped `research_agent/observability.py`, the `propagate_attributes`
  wrapper in `run_agent.py`, and the pytest suite.
- Diagnosed a corrupted Windows install of `langfuse` (same version number, one
  file byte-different from a clean install) that was silently disabling
  instrumentation until `pip install --force-reinstall` was run.
- Generated the initial `docs/trace_evidence.md` skeleton from an exported
  Langfuse JSON dump.

All generated code has been reviewed and the intern can explain it line by
line, per the assignment's rule.

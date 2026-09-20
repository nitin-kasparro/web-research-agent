"""Unit tests for the Firecrawl-backed ADK tools.

Every test mocks the Firecrawl SDK — no live network calls, no real API key
required, no Langfuse account required. Fixtures live in
tests/fixtures/firecrawl_responses.json.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from firecrawl.v2.utils.error_handler import (
    RateLimitError,
    RequestTimeoutError,
)

from research_agent import firecrawl_tools


FIXTURES_PATH = Path(__file__).parent / "fixtures" / "firecrawl_responses.json"
FIXTURES = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))


def _fake_search_response(key: str) -> SimpleNamespace:
    """Turn a fixture dict into an object with the same shape Firecrawl returns."""
    raw = FIXTURES[key]
    web = [SimpleNamespace(**item) for item in raw["web"]]
    return SimpleNamespace(web=web)


def _fake_scrape_response(key: str) -> SimpleNamespace:
    raw = FIXTURES[key]
    return SimpleNamespace(markdown=raw["markdown"], title=raw["title"])


# ---------------------------------------------------------------------------
# search_web
# ---------------------------------------------------------------------------


def test_search_success_returns_normalized_results():
    with patch.object(
        firecrawl_tools.firecrawl, "search", return_value=_fake_search_response("search_success")
    ):
        result = firecrawl_tools.search_web("ai coding assistants", limit=2)

    assert result["status"] == "success"
    assert result["query"] == "ai coding assistants"
    assert result["count"] == 2
    for item in result["results"]:
        assert set(item.keys()) == {"title", "url", "description"}
        assert item["url"].startswith("https://")


def test_search_empty_returns_not_found_without_inventing_sources():
    with patch.object(
        firecrawl_tools.firecrawl, "search", return_value=_fake_search_response("search_empty")
    ):
        result = firecrawl_tools.search_web("nonsense query with no hits")

    assert result["status"] == "not_found"
    assert result["related_pages"] == []
    assert "results" not in result  # do not fabricate a results list


def test_search_rate_limit_returns_controlled_error():
    with patch.object(
        firecrawl_tools.firecrawl,
        "search",
        side_effect=RateLimitError("429 Too Many Requests", status_code=429),
    ):
        result = firecrawl_tools.search_web("anything")

    assert result["status"] == "error"
    assert result["error_type"] == "rate_limit"


# ---------------------------------------------------------------------------
# scrape_web_page
# ---------------------------------------------------------------------------


def test_scrape_success_returns_markdown_and_length():
    with patch.object(
        firecrawl_tools.firecrawl, "scrape", return_value=_fake_scrape_response("scrape_success")
    ):
        result = firecrawl_tools.scrape_web_page("https://example.com/article")

    assert result["status"] == "success"
    assert result["url"] == "https://example.com/article"
    assert result["title"] == "AI Coding Assistants"
    assert result["content_length"] == len(result["markdown"])
    assert result["content_length"] > 0


def test_scrape_invalid_url_is_rejected_before_sdk_call():
    with patch.object(firecrawl_tools.firecrawl, "scrape") as mock_scrape:
        result = firecrawl_tools.scrape_web_page("not a url")

    mock_scrape.assert_not_called()
    assert result["status"] == "error"
    assert result["error_type"] == "invalid_url"


def test_scrape_timeout_and_empty_return_structured_errors():
    # Timeout path
    with patch.object(
        firecrawl_tools.firecrawl,
        "scrape",
        side_effect=RequestTimeoutError("request timed out", status_code=408),
    ):
        timeout_result = firecrawl_tools.scrape_web_page("https://example.com/slow")
    assert timeout_result["status"] == "error"
    assert timeout_result["error_type"] == "timeout"

    # Empty-content path
    with patch.object(
        firecrawl_tools.firecrawl, "scrape", return_value=_fake_scrape_response("scrape_empty")
    ):
        empty_result = firecrawl_tools.scrape_web_page("https://example.com/blank")
    assert empty_result["status"] == "error"
    assert empty_result["error_type"] == "empty_content"


# ---------------------------------------------------------------------------
# Secret safety
# ---------------------------------------------------------------------------


def test_no_firecrawl_or_langfuse_secret_in_repo_source():
    """Grep every committed .py, .md, .json file for real API-key prefixes.

    Fails if any Firecrawl (`fc-...`) or Langfuse (`sk-lf-...` / `pk-lf-...`)
    key leaked into source, tests, docs, or fixtures. `.env` and the venv are
    excluded because they are local-only and gitignored.
    """
    repo_root = Path(__file__).resolve().parents[1]
    banned = [
        re.compile(r"fc-[0-9a-f]{20,}"),
        re.compile(r"sk-lf-[0-9a-f-]{20,}"),
        re.compile(r"pk-lf-[0-9a-f-]{20,}"),
    ]
    skip_dirs = {".venv", "__pycache__", ".git", ".adk", "node_modules"}
    skip_files = {".env"}

    leaks: list[str] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in skip_dirs for part in path.parts):
            continue
        if path.name in skip_files:
            continue
        if path.suffix.lower() not in {".py", ".md", ".json", ".txt", ".yml", ".yaml", ".toml"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in banned:
            if pattern.search(text):
                leaks.append(f"{path.relative_to(repo_root)} matched {pattern.pattern}")

    assert not leaks, "Secret-looking string(s) found in tracked files:\n  " + "\n  ".join(leaks)

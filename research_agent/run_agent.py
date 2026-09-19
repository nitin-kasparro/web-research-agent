"""CLI entry point for the observable web research agent.

Sets up an ADK Runner with an in-memory session, wraps each research turn
in a Langfuse root span with trace-level attributes (name, tags, user_id,
session_id, metadata), streams the ADK events with run_async, and flushes
Langfuse before exit so short-lived CLI processes still ship every trace.
"""
from __future__ import annotations

import asyncio
import os
import uuid

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from langfuse import get_client, propagate_attributes

from research_agent.agent import root_agent
from research_agent.observability import flush_langfuse, setup_observability


APP_NAME = "observable-web-research-agent"
APP_VERSION = "0.1.0"
TRACE_TAGS = ["google-adk", "firecrawl", "beginner-assignment", "local-dev"]


async def run_question(
    runner: Runner,
    user_id: str,
    session_id: str,
    question: str,
) -> str:
    """Run one research turn inside a Langfuse trace and return the final text."""
    langfuse = get_client()
    trace_name = f"research: {question[:60]}"

    with propagate_attributes(
        user_id=user_id,
        session_id=session_id,
        tags=TRACE_TAGS,
        trace_name=trace_name,
        metadata={
            "assignment_level": "beginner",
            "tool_provider": "firecrawl",
            "research_topic": question,
            "app_version": APP_VERSION,
        },
    ):
        with langfuse.start_as_current_observation(
            name="research-request",
            as_type="span",
            input=question,
        ) as span:
            message = types.Content(role="user", parts=[types.Part(text=question)])
            final_text = ""

            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=message,
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    final_text = "".join(part.text or "" for part in event.content.parts)

            span.update(output=final_text)
            return final_text


async def _amain() -> None:
    setup_observability()

    session_service = InMemorySessionService()
    user_id = os.getenv("USER_ID", "intern-user")
    session_id = os.getenv("SESSION_ID", f"session-{uuid.uuid4().hex[:8]}")

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    print("Observable Web Research Agent")
    print(f"  app_name  : {APP_NAME}")
    print(f"  user_id   : {user_id}")
    print(f"  session_id: {session_id}")
    print("Type 'exit' or 'quit' to leave. Follow-ups reuse the same session.\n")

    try:
        while True:
            try:
                question = input("Research question: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not question or question.lower() in {"exit", "quit"}:
                break

            answer = await run_question(runner, user_id, session_id, question)
            print("\n--- Answer ---")
            print(answer)
            print()
    finally:
        flush_langfuse()


def main() -> None:
    asyncio.run(_amain())


if __name__ == "__main__":
    main()

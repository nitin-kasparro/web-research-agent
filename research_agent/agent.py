from google.adk.agents.llm_agent import Agent
from firecrawl import Firecrawl
from firecrawl.v2.utils.error_handler import WebsiteNotSupportedError


from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from research_agent.firecrawl_tools import search_web,scrape_web_page


root_agent = Agent(
    model='gemini-3.5-flash-lite',
    name='root_agent',
     description=(
        "A web research agent that searches for relevant sources, "
        "scrapes selected pages, and produces concise cited research briefs."
    ),
    instruction="""
        You are a web research agent.

        For every research question, you MUST follow these steps in order:

        STEP 1:
        Call search_web exactly once.

        STEP 2:
        Inspect the search results returned by search_web.

        STEP 3:
        Choose at least 2 relevant results from those search results.

        STEP 4:
        Call scrape_web_page separately for EACH of the selected URLs.

        You MUST NOT answer the user's research question until you have
        attempted to scrape at least 2 relevant URLs.

        STEP 5:
        Use the content returned by scrape_web_page to write the answer.

        IMPORTANT:
        - Search results are only for discovering sources.
        - Search result titles and descriptions are NOT evidence.
        - Do not use a source in the final answer unless you successfully
        scraped that source.
        - Do not invent information from a URL that you did not scrape.
        - If a selected URL fails to scrape, select another search result
        and try scraping it.
        - For research questions, the normal tool sequence is:

        search_web
        -> scrape_web_page
        -> scrape_web_page
        -> final answer

        You are a research-only agent. Do not perform actions such as
        booking flights, making purchases, or sending emails.
    """,


    tools=[search_web,scrape_web_page],
)



from google.adk.agents.llm_agent import Agent
from firecrawl import Firecrawl
from firecrawl.v2.utils.error_handler import WebsiteNotSupportedError


from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event


firecrawl = Firecrawl(

)



# Mock tool implementation
def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city."""
    # time zone logic goes here 
    return {"status": "success", "city": city, }

def get_weather_report(city:str) -> dict:
    """Returns the current weather in a specified city."""

    # weather api call goes here 
    return {
        "status":"success",
        "city":city,
        
        
    }

def search_and_read_top_page(query:str)->dict:
    """Find related web pages, read the highest-ranked page, and return its content."""

    results = firecrawl.search(
        query=query
    )

    web_results = results.web or []

    if not web_results:
        return{
            "status":"not found",
            "query":query,
            "related_pages":[]

        }

    result_pages = [
        {
            "title": result.title,
            "url": result.url,
            "description": result.description,

        }

        for result in web_results
    ]

    skipped_pages = []

    # Some search results (for example, maps and protected directory sites)
    # cannot be scraped by Firecrawl. Try the next result instead of failing
    # the entire agent request.
    for page in result_pages[:5]:
        try:
            document = firecrawl.scrape(
                page["url"],
                formats=["markdown"],
                only_main_content=True,
            )

            return {
                "status": "success",
                "query": query,
                "related_pages": result_pages,
                "top_page": {
                    **page,
                    "content": document.markdown or "",
                },
                "skipped_pages": skipped_pages,
            }
        except WebsiteNotSupportedError:
            skipped_pages.append(page)

    return {
        "status": "no_supported_page",
        "query": query,
        "related_pages": result_pages,
        "skipped_pages": skipped_pages,
    }



root_agent = Agent(
    model='gemini-3.6-flash',
    name='root_agent',
    description="Tells the current time in a specified city and Searches the web and summarizes relevant results..",
    instruction=(
        "Answer time and weather questions. "
        "For a research request, call search_and_read_top_page. "
        "Give the user a concise summary of top_page.content, cite its URL, "
        "and list the other related_pages as links. If no page could be "
        "scraped, list the search results and explain that their sites could "
        "not be read."

        
    ),
    tools=[get_current_time,get_weather_report,search_and_read_top_page],
)



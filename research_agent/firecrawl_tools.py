from typing import Any
from urllib.parse import urlparse

from firecrawl import Firecrawl
from firecrawl.v2.utils.error_handler import WebsiteNotSupportedError


firecrawl = Firecrawl(

)


def search_web(query:str, limit:int=5)->dict[str,Any]:
    """Search the web and return candidate sources for research.

    This tool ONLY discovers candidate sources.
    After this tool returns, the agent must inspect the results
    and use scrape_web_page on the relevant URLs before answering.
    """



    if not query.strip():
        return {
            "status": "error",
            "error_type": "invalid_query",
            "message": "Search query cannot be empty.",
        }

    if not 1 <= limit <= 5:
        return {
            "status": "error",
            "error_type": "invalid_limit",
            "message": "limit must be between 1 and 5.",
        }        


    try:
        results = firecrawl.search(query=query)
    except Exception as exc:
        return {
            "status": "error",
            "error_type": "search_failed",
            "message": str(exc),
        }


    web_results = results.web or []

    if not web_results:
        return{
            "status":"not found",
            "query":query,
            "related_pages":[]

        }

    normalized_results = []

    for result in web_results[:limit]:
        normalized_results.append(
            {
                "title": result.title or "",
                "url": result.url or "",
                "description": result.description or "",
            }
        )


    return{
        "status":"success",
        "query":query,
        "count":len(normalized_results),
        "results":normalized_results
    }




def scrape_web_page(url: str) -> dict[str, Any]:
    """Scrape the complete main content of one selected web page.

    Use this tool after search_web to retrieve the actual content
    of a source that will be used as evidence.

    The agent should call this tool separately for each selected
    source URL.
    """

    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return {
            "status": "error",
            "error_type": "invalid_url",
            "url": url,
            "message": "URL must be a valid HTTP or HTTPS URL.",
        }

    try:
        document = firecrawl.scrape(
            url,
            formats=["markdown"],
            only_main_content=True,
        )

        markdown = document.markdown or ""

        if not markdown.strip():
            return {
                "status": "error",
                "error_type": "empty_content",
                "url": url,
                "message": "Firecrawl returned empty content.",
            }

        return {
            "status": "success",
            "url": url,
            "title": getattr(document, "title", None) or "",
            "markdown": markdown,
            "content_length": len(markdown),
        }

    except WebsiteNotSupportedError:
        return {
            "status": "error",
            "error_type": "website_not_supported",
            "url": url,
            "message": "Firecrawl does not support scraping this website.",
        }

    except Exception as exc:
        return {
            "status": "error",
            "error_type": "scrape_failed",
            "url": url,
            "message": str(exc),
        }
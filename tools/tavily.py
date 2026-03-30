from langchain_tavily import TavilySearch


def tavily_search(query: str, max_results: int = 5) -> list[dict]:

    tool = TavilySearch(max_results=max_results)

    results = tool.invoke({"query": query})

    normalised: list[dict] = []

    for r in results.get("results", []) or []:
        normalised.append(
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "published_at": r.get("published_at", "") or r.get("published_date", ""),
                "snippet": r.get("snippet", "") or r.get("content", ""),
                "source": r.get("source", ""),
            }
        )
        
    return normalised
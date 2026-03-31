from typing import List
from langchain_tavily import TavilySearch
import os


def tavily_search(query: str, max_results: int = 5) -> List[dict]:

    tool = TavilySearch(max_results=max_results)

    results = tool.invoke({"query": query})

    normalised: List[dict] = []

    for r in results.get("results", []) or []:
        normalised.append(
            {
                "title": r.get("title") or "",
                "url": r.get("url") or "",
                "published_at": r.get("published_at") or r.get("published_date"),
                "snippet": r.get("snippet") or r.get("content") or "",
                "source": r.get("source"),
            }
        )

    return normalised



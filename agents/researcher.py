from workflow.settings import llm_researcher
from schemas.state import State
from schemas.plan import Plan
from tools.tavily import tavily_search
from schemas.evidence import EvidencePack, EvidenceItem
from langsmith import traceable
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Optional, List
from datetime import date, timedelta

def _iso_to_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except Exception:
        return None


RESEARCH_PROMPT = """You are a research synthesizer for technical writing.

Given raw web search results, produce a deduplicated list of EvidenceItem objects.

Rules:
- Only include items with a non-empty url.
- Prefer relevant + authoritative sources (company blogs, docs, reputable outlets).
- If a published date is explicitly present in the result payload, keep it as YYYY-MM-DD.
  If missing or unclear, set published_at=null. Do NOT guess.
- Keep snippets short.
- Deduplicate by URL.
"""


@traceable(name="researcher")
def research_node(state: State) -> dict:

    queries = (state.get("queries", []) or [])[:10]
    max_results = 6

    raw_results: List[dict] = []

    for q in queries:
        raw_results.extend(tavily_search(q, max_results=max_results))

    if not raw_results:
        return {"evidence": []}
    
    extractor = llm_researcher.with_structured_output(EvidencePack)

    pack = extractor.invoke(
        [
            SystemMessage(content=RESEARCH_PROMPT),
            HumanMessage(
                content=(
                    f"As_of date: {state['as_of']}\n"
                    f"Recency days: {state['recency_days']}\n\n"
                    f"Raw search results:\n{raw_results}"
                )
            ),
        ]
    )


    # deduplicate by URL
    seen_urls = {}
    for e in pack.evidence:
        if e.url:
            seen_urls[e.url] = e

    evidence = list(seen_urls.values())

    if state.get("mode") == "open_book":
        as_of = date.fromisoformat(state["as_of"])
        cutoff = as_of - timedelta(days=int(state["recency_days"]))
        evidence = [e for e in evidence if (d := _iso_to_date(e.published_at)) and d >= cutoff]

    return {"evidence": evidence}
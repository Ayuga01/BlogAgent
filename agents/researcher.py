from workflow.settings import llm_researcher
from schemas.state import State
from schemas.plan import Plan
from tools.tavily import tavily_search
from schemas.evidence import EvidencePack
from langsmith import traceable
from langchain_core.messages import SystemMessage, HumanMessage

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

    queries = (state.get("queries", []) or [])
    max_results = 6

    raw_results: list[dict] = []

    for q in queries:
        raw_results.extend(tavily_search(q, max_results=max_results))

    if not raw_results:
        return {"evidence": []}
    
    extractor = llm_researcher.with_structured_output(EvidencePack)

    pack = extractor.invoke(
        [
            SystemMessage(content=RESEARCH_PROMPT),
            HumanMessage(content=f"Raw search results:\n{raw_results}")
        ]
    )


    # deduplicate by URL
    seen_urls = {}
    for e in pack.evidence:
        if e.url:
            seen_urls[e.url] = e

    return {"evidence": list(seen_urls.values())}
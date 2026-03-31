from workflow.settings import llm_worker
from schemas.state import State
from schemas.plan import Task
from schemas.evidence import EvidenceItem
from schemas.plan import Plan
from langsmith import traceable
from langgraph.types import Send
from langchain_core.messages import SystemMessage, HumanMessage


@traceable(name="fanout")
def fanout(state: State):
    assert state["plan"] is not None
    return [Send("worker", 
                 {
                    "task": task.model_dump(),
                    "topic": state["topic"],
                    "mode": state["mode"],
                    "as_of": state["as_of"],
                    "recency_days": state["recency_days"],
                    "plan": state["plan"].model_dump(),
                    "evidence": [e.model_dump() for e in state.get("evidence", [])],
                },
            )
            for task in state["plan"].tasks]



WORKER_PROMPT = """You are a senior technical writer and developer advocate.
                    Write ONE section of a technical blog post in Markdown.

                    Constraints:
                    - Cover ALL bullets in order.
                    - Target words ±15%.
                    - Output only section markdown starting with "## <Section Title>".

                    Scope guard:
                    - If blog_kind=="news_roundup", do NOT drift into tutorials (scraping/RSS/how to fetch).
                    Focus on events + implications.

                    Grounding:
                    - If mode=="open_book": do not introduce any specific event/company/model/funding/policy claim unless supported by provided Evidence URLs.
                    For each supported claim, attach a Markdown link ([Source](URL)).
                    If unsupported, write "Not found in provided sources."
                    - If requires_citations==true (hybrid tasks): cite Evidence URLs for external claims.

                    Code:
                    - If requires_code==true, include at least one minimal snippet.
                """


@traceable(name="worker")
def worker(payload: dict) -> dict:

    task = Task(**payload["task"])
    plan = Plan(**payload["plan"])
    evidence = [EvidenceItem(**e) for e in payload.get("evidence", [])]

    bullets_text = "\n- " + "\n- ".join(task.bullets)
    evidence_text = ""

    if evidence:
        evidence_text = "\n".join(
            f"- {e.title} | {e.url} | {e.published_at or 'date:unknown'}".strip()
            for e in evidence[:20]
        )

    section_md = llm_worker.invoke(
        [
            SystemMessage(content=WORKER_PROMPT),
            HumanMessage(content=(
                f"Blog title: {plan.blog_title}\n"
                f"Audience: {plan.audience}\n"
                f"Tone: {plan.tone}\n"
                f"Blog kind: {plan.blog_kind}\n"
                f"Constraints: {plan.constraints}\n"
                f"Topic: {payload['topic']}\n"
                f"Mode: {payload.get('mode')}\n"
                f"As-of: {payload.get('as_of')} (recency_days={payload.get('recency_days')})\n\n"
                f"Section title: {task.title}\n"
                f"Goal: {task.goal}\n"
                f"Target words: {task.target_words}\n"
                f"Tags: {task.tags}\n"
                f"requires_research: {task.requires_research}\n"
                f"requires_citations: {task.requires_citations}\n"
                f"requires_code: {task.requires_code}\n"
                f"Bullets:{bullets_text}\n\n"
                f"Evidence (ONLY cite these URLs):\n{evidence_text}\n"
            ))
        ]
    ).content.strip()

    return {"sections": [(task.id, section_md)]}
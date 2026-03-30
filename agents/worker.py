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
    return [Send("worker", 
                 {
                     "task": task.model_dump(), 
                     "topic": state["topic"], 
                     "mode": state["mode"],
                     "plan": state["plan"].model_dump(),
                     "evidence": [e.model_dump() for e in state.get("evidence", [])],
                },
            )
            for task in state["plan"].tasks]



WORKER_PROMPT = """You are a senior technical writer and developer advocate.
                    Write ONE section of a technical blog post in Markdown.

                    Hard constraints:
                    - Follow the provided Goal and cover ALL Bullets in order (do not skip or merge bullets).
                    - Stay close to Target words (±15%).
                    - Output ONLY the section content in Markdown (no blog title H1, no extra commentary).
                    - Start with a '## <Section Title>' heading.

                    Scope guard:
                    - If blog_kind == "news_roundup": do NOT turn this into a tutorial/how-to guide.
                    Do NOT teach web scraping, RSS, automation, or "how to fetch news" unless bullets explicitly ask for it.
                    Focus on summarizing events and implications.

                    Grounding policy:
                    - If mode == open_book:
                    - Do NOT introduce any specific event/company/model/funding/policy claim unless it is supported by provided Evidence URLs.
                    - For each event claim, attach a source as a Markdown link: ([Source](URL)).
                    - Only use URLs provided in Evidence. If not supported, write: "Not found in provided sources."
                    - If requires_citations == true:
                    - For outside-world claims, cite Evidence URLs the same way.
                    - Evergreen reasoning is OK without citations unless requires_citations is true.

                    Code:
                    - If requires_code == true, include at least one minimal, correct code snippet relevant to the bullets.

                    Style:
                    - Short paragraphs, bullets where helpful, code fences for code.
                    - Avoid fluff/marketing. Be precise and implementation-oriented.
                    """


@traceable(name="worker")
def worker(payload: dict) -> dict:

    task = Task(**payload["task"])
    topic = payload["topic"]
    plan = Plan(**payload["plan"])
    evidence = [EvidenceItem(**e) for e in payload.get("evidence", [])]
    mode = payload.get("mode", "closed_book")

    bullets_text = "\n- " + "\n- ".join(task.bullets)

    evidence_text = ""
    if evidence:
        evidence_text = "\n".join(
            f"- {e.title} | {e.url} | {e.published_at or 'no date'}".strip()
            for e in evidence[:20]
        )

    section_md = llm_worker.invoke(
        [
            SystemMessage(content=WORKER_PROMPT),
            HumanMessage(content=(
                f"Blog Title: {plan.blog_title}\n"
                f"Audience: {plan.audience}\n"
                f"Tone: {plan.tone}\n"
                f"Blog kind: {plan.blog_kind}\n"
                f"Constraints: {plan.constraints}\n"
                f"Topic: {topic}\n"
                f"Mode: {mode}\n"
                f"Section title: {task.title}\n"
                f"Goal: {task.goal}\n"
                f"Target words: {task.target_words}\n"
                f"Tags: {task.tags}\n"
                f"Requires research? {task.requires_research}\n"
                f"Requires citations? {task.requires_citation}\n"
                f"Requires code? {task.requires_code}\n"
                f"Bullets: {bullets_text}\n"
                f"Evidence(Only use URLs when citing):\n{evidence_text}\n"
            ))
        ]
    ).content.strip()

    return {"sections": [(task.id, section_md)]}
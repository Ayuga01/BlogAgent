from workflow.settings import llm_orchestrator
from langsmith import traceable
from schemas.state import State
from schemas.plan import Plan
from langchain_core.messages import SystemMessage, HumanMessage


ORCHESTRATOR_PROMPT = """You are a senior technical writer and developer advocate.
                            Produce a highly actionable outline for a technical blog post.

                            Requirements:
                            - 5–9 tasks, each with goal + 3–6 bullets + target_words.
                            - Tags are flexible; do not force a fixed taxonomy.

                            Grounding:
                            - closed_book: evergreen, no evidence dependence.
                            - hybrid: use evidence for up-to-date examples; mark those tasks requires_research=True and requires_citations=True.
                            - open_book: weekly/news roundup:
                            - Set blog_kind="news_roundup"
                            - No tutorial content unless requested
                            - If evidence is weak, plan should explicitly reflect that (don’t invent events).

                            Output must match Plan schema.
                            """

@traceable(name="orchestrator")
def orchestrator(state: State) -> dict:

    planner_llm = llm_orchestrator.with_structured_output(Plan)

    evidence = state.get("evidence", [])
    mode = state.get("mode", "closed_book")

    forced_kind = "news_roundup" if mode == "open_book" else None

    plan = planner_llm.invoke(
        [
            SystemMessage(content=ORCHESTRATOR_PROMPT),
            HumanMessage(
                content=(
                    f"Topic: {state['topic']}\n"
                    f"Mode: {mode}\n"
                    f"As-of: {state['as_of']}(recency_days: {state['recency_days']})\n"
                    f"{'Force blog_kind=news_roundup' if forced_kind else ''}\n\n"
                    f"Evidence (if any):\n{[e.model_dump() for e in evidence][::16]}"
                )
            ),
        ]
    )

    if forced_kind:
        plan.blog_kind = "news_roundup"

    return {"plan": plan}
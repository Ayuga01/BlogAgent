from workflow.settings import llm_planner
from langsmith import traceable
from schemas.state import State
from schemas.plan import Plan
from langchain_core.messages import SystemMessage, HumanMessage


ORCHESTRATOR_PROMPT = """You are a senior technical writer and developer advocate.
                        Your job is to produce a highly actionable outline for a technical blog post.

                        Hard requirements:
                        - Create 5–9 sections (tasks) suitable for the topic and audience.
                        - Each task must include:
                        1) goal (1 sentence)
                        2) 3–6 bullets that are concrete, specific, and non-overlapping
                        3) target word count (120–550)

                        Quality bar:
                        - Assume the reader is a developer; use correct terminology.
                        - Bullets must be actionable: build/compare/measure/verify/debug.
                        - Ensure the overall plan includes at least 2 of these somewhere:
                        * minimal code sketch / MWE (set requires_code=True for that section)
                        * edge cases / failure modes
                        * performance/cost considerations
                        * security/privacy considerations (if relevant)
                        * debugging/observability tips

                        Grounding rules:
                        - Mode closed_book: keep it evergreen; do not depend on evidence.
                        - Mode hybrid:
                        - Use evidence for up-to-date examples (models/tools/releases) in bullets.
                        - Mark sections using fresh info as requires_research=True and requires_citations=True.
                        - Mode open_book:
                        - Set blog_kind = "news_roundup".
                        - Every section is about summarizing events + implications.
                        - DO NOT include tutorial/how-to sections unless user explicitly asked for that.
                        - If evidence is empty or insufficient, create a plan that transparently says "insufficient sources"
                            and includes only what can be supported.

                        Output must strictly match the Plan schema.
                        """

@traceable(name="orchestrator")
def orchestrator(state: State) -> dict:

    planner_llm = llm_planner.with_structured_output(Plan)

    evidence = state.get("evidence", [])
    mode = state.get("mode", "closed_book")

    plan = planner_llm.invoke(
        [
            SystemMessage(content=ORCHESTRATOR_PROMPT),
            HumanMessage(
                content=(
                    f"Topic: {state['topic']}\n"
                    f"Mode: {mode}\n"
                    f"Evidence (if any):\n"
                    f"{[e.model_dump() for e in evidence][::16]}"
                )
            ),
        ]
    )

    return {"plan": plan}
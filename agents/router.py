from workflow.settings import llm_router
from langsmith import traceable
from schemas.state import State
from schemas.routerschema import RouterDecision
from langchain_core.messages import SystemMessage, HumanMessage

ROUTER_PROMPT = """You are a routing module for a technical blog planner.

Decide whether web research is needed BEFORE planning.

Modes:
- closed_book (needs_research=false):
  Evergreen topics where correctness does not depend on recent facts (concepts, fundamentals).
- hybrid (needs_research=true):
  Mostly evergreen but needs up-to-date examples/tools/models to be useful.
- open_book (needs_research=true):
  Mostly volatile: weekly roundups, "this week", "latest", rankings, pricing, policy/regulation.

If needs_research=true:
- Output 3–10 high-signal queries.
- Queries should be scoped and specific (avoid generic queries like just "AI" or "LLM").
- If user asked for "last week/this week/latest", reflect that constraint IN THE QUERIES.
"""

@traceable(name="router_node")
def router_node(state: State) -> dict:

    topic = state["topic"]
    decider = llm_router.with_structured_output(RouterDecision)

    decision = decider.invoke(
        [
            SystemMessage(content=ROUTER_PROMPT),
            HumanMessage(content=f"Topic: {topic}")
        ]
    )

    return {
        "needs_research": decision.needs_research,
        "mode": decision.mode,
        "queries": decision.queries
    }

@traceable(name="router_decision")
def route_next(state: State) -> str:
    
    if state["needs_research"]:
        return "researcher"
    else:
        return "orchestrator"

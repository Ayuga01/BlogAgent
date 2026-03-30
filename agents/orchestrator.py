from workflow.settings import llm_planner
from langsmith import traceable
from schemas.state import State
from schemas.plan import Plan
from langchain_core.messages import SystemMessage, HumanMessage

@traceable(name="orchestrator")
def orchestrator(state: State) -> dict:

    planner_llm = llm_planner.with_structured_output(Plan)
    plan = planner_llm.invoke(
        [
            SystemMessage(content="Create a research plan for the given topic. Break down the topic into 5-7 sections."),
            HumanMessage(content=f"Topic: {state['topic']}"),
        ]
    )

    return {"plan": plan}
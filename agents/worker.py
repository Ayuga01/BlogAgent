from workflow.settings import llm_worker
from schemas.state import State
from schemas.plan import Plan
from langsmith import traceable
from langgraph.types import Send
from langchain_core.messages import SystemMessage, HumanMessage


@traceable(name="fanout")
def fanout(state: State):
    return [Send("worker", {"task": task, "topic": state["topic"], "plan": state["plan"]})
            for task in state["plan"].tasks]



@traceable(name="worker")
def worker(payload: dict) -> dict:
    task = payload["task"]
    topic = payload["topic"]
    plan = payload["plan"]

    blog_title = plan.blog_title

    section_md = llm_worker.invoke(
        [
            SystemMessage(content="Write a clean markdown section."),
            HumanMessage(content=(
                f"Blog Title: {blog_title}\n"
                f"Topic: {topic}\n"
                f"Section: {task.title}\n"
                f"Brief: {task.brief}\n\n"
                "Return only the section content in the Markdown."
            ))
        ]
    ).content.strip()

    return {"sections": [section_md]}
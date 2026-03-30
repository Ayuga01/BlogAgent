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

    bullets_text = "\n- " + "\n- ".join(task.bullets)

    blog_title = plan.blog_title

    section_md = llm_worker.invoke(
        [
            SystemMessage(
                content="You are a senior technical writer and developer advocate. Write ONE section of a technical blog post in Markdown.\n\n"
                        "Hard constraints:\n"
                        "- Follow the provided Goal and cover ALL Bullets in order (do not skip or merge bullets).\n"
                        "- Stay close to the Target words (±15%).\n"
                        "- Output ONLY the section content in Markdown (no blog title H1, no extra commentary).\n\n"
                        "Technical quality bar:\n"
                        "- Be precise and implementation-oriented (developers should be able to apply it).\n"
                        "- Prefer concrete details over abstractions: APIs, data structures, protocols, and exact terms.\n"
                        "- When relevant, include at least one of:\n"
                        "  * a small code snippet (minimal, correct, and idiomatic)\n"
                        "  * a tiny example input/output\n"
                        "  * a checklist of steps\n"
                        "  * a diagram described in text (e.g., 'Flow: A -> B -> C')\n"
                        "- Explain trade-offs briefly (performance, cost, complexity, reliability).\n"
                        "- Call out edge cases / failure modes and what to do about them.\n"
                        "- If you mention a best practice, add the 'why' in one sentence.\n\n"
                        "Markdown style:\n"
                        "- Start with a '## <Section Title>' heading.\n"
                        "- Use short paragraphs, bullet lists where helpful, and code fences for code.\n"
                        "- Avoid fluff. Avoid marketing language.\n"
                        "- If you include code, keep it focused on the bullet being addressed.\n"
                                ),
            HumanMessage(content=(
                f"Blog Title: {blog_title}\n"
                f"Audience: {plan.audience}\n"
                f"Tone: {plan.tone}\n"
                f"Topic: {topic}\n"
                f"Section: {task.title}\n"
                f"Section_type: {task.section_type}\n"
                f"Goal: {task.goal}\n"
                f"Bullets: {bullets_text}\n"
                f"Target words: {task.target_words}"
                "Return only the section content in the Markdown."
            ))
        ]
    ).content.strip()

    return {"sections": [section_md]}
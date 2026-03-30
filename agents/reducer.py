from pathlib import Path
from langsmith import traceable
from schemas import plan, state
from schemas.state import State


@traceable(name="reducer")
def reducer(state: State) ->dict:


    plan = state["plan"]

    ordered_sections = [md for _, md in sorted(state["sections"], key=lambda x: x[0])]
    body = "\n\n".join(ordered_sections).strip()
    final_md = f"# {plan.blog_title}\n\n{body}\n"

    file_name = f"{plan.blog_title}.md"

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True) 

    output_path = output_dir / file_name

    output_path.write_text(final_md, encoding="utf-8")

    return {"final": final_md}
from pathlib import Path
from langsmith import traceable
from schemas.state import State


@traceable(name="reducer")
def reducer(state: State) ->dict:

    title = state["plan"].blog_title
    body = "\n\n".join(state["sections"]).strip()

    final_md = f"# {title}\n\n{body}\n"

    filename = "".join(c if c.isalnum() or c in (" ", "_", "-") else "" for c in title)
    filename = filename.strip().lower().replace(" ", "_")+".md"
    
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True) 

    output_path = output_dir / filename

    output_path.write_text(final_md, encoding="utf-8")

    return {"final": final_md}
from pydantic import BaseModel, Field
from typing import List, Annotated, Literal
from dotenv import load_dotenv

load_dotenv()

class Task(BaseModel):
    id: int
    title: str
    goal: str = Field(..., description="one sentence describing what the reader should be able to do/understand after this section.")
    bullets: List[str] = Field(...,
                               min_length=3,
                               max_length=5,
                               description="3-5 non-overlapping subpoints to cover in the section. These should be distinct and not repetitive. They should also not be too detailed, as they are meant to be expanded upon in the section content.")
    target_words: int = Field(..., description="The ideal word count for the section content(120-450)")
    section_type: Literal["introduction", "core", "examples", "checklist", "common_mistakes", "conclusion"] = Field(..., description="Use common_mistakes exactly once in the plan.")

class Plan(BaseModel):
    blog_title: str
    audience: str = Field(..., description="Who the blog is for")
    tone: str = Field(..., description="Writing tone(e.g. professional, casual, humorous, crisp, etc)")
    tasks: List[Task]
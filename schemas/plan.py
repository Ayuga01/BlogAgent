from __future__ import annotations
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
    tags: List[str] = Field(default_factory=list)
    requires_research: bool = False
    requires_citation: bool = False
    requires_code: bool = False

class Plan(BaseModel):
    blog_title: str
    audience: str
    tone: str
    blog_kind: Literal["explainer", "how-to", "comparison", "case-study", "tutorial", "system_design", "other"] = "explainer"
    constraints: List[str] = Field(default_factory=list)
    tasks: List[Task]
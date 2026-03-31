from __future__ import annotations
from pydantic import AliasChoices, BaseModel, Field
from typing import List, Annotated, Literal
from dotenv import load_dotenv

load_dotenv()

class Task(BaseModel):
    id: int
    title: str
    goal: str = Field(..., description="one sentence describing what the reader should be able to do/understand after this section.")
    bullets: List[str] = Field(...,min_length=3, max_length=6,)
    target_words: int = Field(..., description="Target words(120-650)")
    tags: List[str] = Field(default_factory=list)
    requires_research: bool = False
    requires_citations: bool = False
    requires_code: bool = False

class Plan(BaseModel):
    blog_title: str
    audience: str
    tone: str
    blog_kind: Literal["explainer", "how-to", "comparison", "case-study", "tutorial", "system_design", "news_roundup", "other"] = "explainer"
    constraints: List[str] = Field(default_factory=list)
    tasks: List[Task]

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Annotated, Literal

class RouterDecision(BaseModel):
    needs_research: bool
    mode: Literal["closed_book", "open_book", "hybrid"]
    queries: List[str] = Field(default_factory=list)
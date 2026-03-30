from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Annotated, Literal, Optional
from dotenv import load_dotenv

class EvidenceItem(BaseModel):
    title: str
    url: str
    published_at: Optional[str] = None
    snippet: Optional[str] = None
    source: Optional[str] = None

class EvidencePack(BaseModel):
    evidence: List[EvidenceItem] = Field(default_factory=list)
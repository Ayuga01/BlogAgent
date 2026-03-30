from typing import TypedDict, List, Annotated, Literal, Optional
from schemas.plan import Plan
from schemas.evidence import EvidenceItem
import operator

class State(TypedDict):
    topic: str
    mode: str
    needs_research: bool
    queries: List[str]
    evidence: List[EvidenceItem]
    plan: Optional[Plan]

    sections: Annotated[List[tuple[int, str]], operator.add]
    final: str
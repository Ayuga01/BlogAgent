from typing import TypedDict, List, Annotated, Literal, Optional
from schemas.plan import Plan
import operator

class State(TypedDict):
    topic: str
    plan = Plan
    sections: Annotated[List[str], operator.add]
    final: str
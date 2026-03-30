from langgraph.graph import StateGraph, START, END
from agents.orchestrator import orchestrator
from agents.worker import worker, fanout
from agents.reducer import reducer
from schemas.state import State

builder = StateGraph(State)

builder.add_node("orchestrator", orchestrator)
builder.add_node("worker", worker)
builder.add_node("reducer", reducer)


builder.add_edge(START, "orchestrator")
builder.add_conditional_edges("orchestrator", fanout, ["worker"])
builder.add_edge("worker", "reducer")
builder.add_edge("reducer", END)

app = builder.compile()



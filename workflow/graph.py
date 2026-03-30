from langgraph.graph import StateGraph, START, END
from agents.orchestrator import orchestrator
from agents.worker import worker, fanout
from agents.reducer import reducer
from agents.router import router_node, route_next
from agents.researcher import research_node
from schemas.state import State

builder = StateGraph(State)

builder.add_node("router", router_node)
builder.add_node("researcher", research_node)
builder.add_node("orchestrator", orchestrator)
builder.add_node("worker", worker)
builder.add_node("reducer", reducer)


builder.add_edge(START, "router")
builder.add_conditional_edges("router", route_next, {"researcher": "researcher", "orchestrator": "orchestrator"})
builder.add_edge("researcher", "orchestrator")

builder.add_conditional_edges("orchestrator", fanout, ["worker"])
builder.add_edge("worker", "reducer")
builder.add_edge("reducer", END)

app = builder.compile()



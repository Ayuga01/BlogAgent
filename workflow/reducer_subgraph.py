from langgraph.graph import StateGraph, START, END
from agents.reducer import generate_and_place_images, merge_content, decide_images, finalize_without_images
from schemas.state import State


def _route_after_merge(state: State) -> str:
    if state.get("skip_images", False):
        return "finalize_without_images"
    return "decide_images"


def _route_after_decide(state: State) -> str:
    if not state.get("image_specs"):
        return "finalize_without_images"
    return "generate_and_place_images"


reducer_builder = StateGraph(State)
reducer_builder.add_node("merge_content", merge_content)
reducer_builder.add_node("decide_images", decide_images)
reducer_builder.add_node("generate_and_place_images", generate_and_place_images)
reducer_builder.add_node("finalize_without_images", finalize_without_images)

reducer_builder.add_edge(START, "merge_content")
reducer_builder.add_conditional_edges("merge_content", _route_after_merge, {
    "decide_images": "decide_images",
    "finalize_without_images": "finalize_without_images",
})
reducer_builder.add_conditional_edges("decide_images", _route_after_decide, {
    "generate_and_place_images": "generate_and_place_images",
    "finalize_without_images": "finalize_without_images",
})
reducer_builder.add_edge("generate_and_place_images", END)
reducer_builder.add_edge("finalize_without_images", END)

reducer = reducer_builder.compile()
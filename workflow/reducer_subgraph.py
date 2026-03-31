from langgraph.graph import StateGraph, START, END
from agents.reducer import generate_and_place_images, merge_content, decide_images
from schemas.state import State


reducer_builder = StateGraph(State)
reducer_builder.add_node("merge_content", merge_content)
reducer_builder.add_node("decide_images", decide_images)
reducer_builder.add_node("generate_and_place_images", generate_and_place_images)

reducer_builder.add_edge(START, "merge_content")
reducer_builder.add_edge("merge_content", "decide_images")
reducer_builder.add_edge("decide_images", "generate_and_place_images")
reducer_builder.add_edge("generate_and_place_images", END)

reducer = reducer_builder.compile()
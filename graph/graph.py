from langgraph.graph import END, StateGraph

from graph._node import (
    decide_debate, decide_route,
    node_advocatus, node_archivist, node_chronologist,
    node_il_capo_compile, node_il_capo_route, node_il_capo_chat,
    node_legalist, node_legalist_rebuttal
)
from graph.state import FalconeState

# Build the state graph with FalconeState
builder = StateGraph(FalconeState)

# ----- Pipeline nodes -----
builder.add_node("il_capo_route", node_il_capo_route)       # Initial router
builder.add_node("il_capo_chat", node_il_capo_chat)         # Direct chat mode
builder.add_node("archivist", node_archivist)               # Fact extraction
builder.add_node("chronologist", node_chronologist)         # Timeline construction
builder.add_node("legalist", node_legalist)                 # Legal violation mapping
builder.add_node("advocatus", node_advocatus)               # Stress-testing findings
builder.add_node("il_capo_compile", node_il_capo_compile)   # Final report compilation
builder.add_node("legalist_rebuttal", node_legalist_rebuttal)  # Legalist rebuttal

# ----- Graph flow -----
builder.set_entry_point("il_capo_route")
builder.add_conditional_edges(
    "il_capo_route",
    decide_route,
    {
        "investigate": "archivist",
        "chat": "il_capo_chat"
    }
)

# Direct chat path
builder.add_edge("il_capo_chat", END)

# Full investigation path
builder.add_edge("archivist", "chronologist")
builder.add_edge("chronologist", "legalist")
builder.add_edge("legalist", "advocatus")
builder.add_conditional_edges(
    "advocatus",
    decide_debate,
    {
        "rebuttal": "legalist_rebuttal",
        "compile": "il_capo_compile"
    }
)
builder.add_edge("legalist_rebuttal", "advocatus")
builder.add_edge("il_capo_compile", END)

# Compile the graph
graph = builder.compile()
from typing import TypedDict, Annotated
import operator

class FalconeState(TypedDict):
    """
    State that flows through the Falcone investigation graph.
    Every node can read and add data to this state.
    """
    query: str                           # User query
    file_path: str | None                # Path of uploaded file (if any)
    retrieved_chunks: list[dict]         # Retrieval results (currently unused)
    archivist_facts: dict                # Facts extracted by Archivist
    chronologist_output: dict            # Timeline and analysis from Chronologist
    legalist_output: dict                # Legal violations found by Legalist
    advocatus_output: dict               # Challenges from Advocatus Diaboli
    legalist_rebuttal: dict              # Rebuttal from Legalist (if any)
    debate_rounds: int                   # Number of debate rounds already completed
    routing: dict                        # Il Capo's routing decision
    final_report: str                    # Final investigation report
    messages: Annotated[list, operator.add]  # Messages for UI / log
    conversation_history: list[dict]     # User conversation history
    cached_investigation: dict           # Cached investigation results for follow-up
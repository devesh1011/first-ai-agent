"""When we define a LangGraph StateGraph, we use a state schema.

The state schema represents the structure and types of data that our graph will use.

All nodes are expected to communicate with that schema.

LangGraph offers flexibility in how you define your state schema, accommodating various Python types and validation approaches!"""

import random
from typing import Literal
from langgraph.graph import StateGraph
from pydantic import BaseModel, field_validator, ValidationError
from langgraph.graph import START, END

"""Pydantic
As mentioned, TypedDict and dataclasses provide type hints but they don't enforce types at runtime.

This means you could potentially assign invalid values without raising an error!

For example, we can set mood to mad even though our type hint specifies mood: list[Literal["happy","sad"]]"""


class PydanticState(BaseModel):
    name: str
    mood: str

    @field_validator("mood")
    @classmethod
    def validate_mood(cls, value):
        # Ensure the mood is either "happy" or "sad"
        if value not in ["happy", "sad"]:
            raise ValueError("Each mood must be either 'happy' or 'sad'")
        return value


try:
    state = PydanticState(name="John Doe", mood="mad")
except ValidationError as e:
    print("Validation Error:", e)


def node_1(state):
    print("---Node 1---")
    return {"name": state["name"] + " is ... "}


def node_2(state):
    print("---Node 2---")
    return {"mood": "happy"}


def node_3(state):
    print("---Node 3---")
    return {"mood": "sad"}


def decide_mood(state) -> Literal["node_2", "node_3"]:

    # Here, let's just do a 50 / 50 split between nodes 2, 3
    if random.random() < 0.5:

        # 50% of the time, we return Node 2
        return "node_2"

    # 50% of the time, we return Node 3
    return "node_3"


builder = StateGraph(PydanticState)
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_node("node_3", node_3)

# Logic
builder.add_edge(START, "node_1")
builder.add_conditional_edges("node_1", decide_mood)
builder.add_edge("node_2", END)
builder.add_edge("node_3", END)

# Add
graph = builder.compile()

print(graph.invoke(PydanticState(name="Lance", mood="sad")))

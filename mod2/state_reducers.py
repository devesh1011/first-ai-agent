"""Now, we're going to dive into reducers, which specify how state updates are performed on specific keys / channels in the state schema."""

"""Branching
Let's look at a case where our nodes branch."""

from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END


# class State(TypedDict):
#     foo: int


# def node_1(state):
#     print(f"----NODE1____")
#     return {"foo": state["foo"] + 1}


# def node_2(state):
#     print("---Node2---")
#     return {"foo": state["foo"] + 1}


# def node_3(state):
#     print("---Node3---")
#     return {"foo": state["foo"] + 1}


# # build graph
# builder = StateGraph(State)
# builder.add_node("node_1", node_1)
# builder.add_node("node_2", node_2)
# builder.add_node("node_3", node_3)

# # Logic
# builder.add_edge(START, "node_1")
# builder.add_edge("node_1", "node_2")
# builder.add_edge("node_1", "node_3")
# builder.add_edge("node_2", END)
# builder.add_edge("node_3", END)

# # Add
# graph = builder.compile()

# from langgraph.errors import InvalidUpdateError

# try:
#     graph.invoke({"foo": 1})
# except InvalidUpdateError as e:
#     print(f"{e}")


"""We see a problem!

Node 1 branches to nodes 2 and 3.

Nodes 2 and 3 run in parallel, which means they run in the same step of the graph.

They both attempt to overwrite the state within the same step.

This is ambiguous for the graph! Which state should it keep?"""

"""Reducers
Reducers give us a general way to address this problem.

They specify how to perform updates.

We can use the Annotated type to specify a reducer function."""

# from operator import add
# from typing import Annotated


# class State(TypedDict):
#     foo: Annotated[list[int], add]


# def node_1(state):
#     print("---Node 1---")
#     return {"foo": [state["foo"][-1] + 1]}


# def node_2(state):
#     print("---Node 2---")
#     return {"foo": [state["foo"][-1] + 1]}


# def node_3(state):
#     print("---Node 3---")
#     return {"foo": [state["foo"][-1] + 1]}


# # Build graph
# builder_2 = StateGraph(State)
# builder_2.add_node("node_1", node_1)
# builder_2.add_node("node_2", node_2)
# builder_2.add_node("node_3", node_3)

# # Logic
# builder_2.add_edge(START, "node_1")
# builder_2.add_edge("node_1", "node_2")
# builder_2.add_edge("node_1", "node_3")
# builder_2.add_edge("node_2", END)
# builder_2.add_edge("node_3", END)


# # Add
# graph = builder_2.compile()

# print(graph.invoke({"foo": [1]}))

"""Custom Reducers
To address cases like this, we can also define custom reducers.

For example, lets define custom reducer logic to combine lists and handle cases where either or both of the inputs might be None."""


# def reduce_list(left: list | None, right: list | None) -> list:
#     """Safely combine two lists, handling cases where either or both inputs might be None.

#     Args:
#         left (list | None): The first list to combine, or None.
#         right (list | None): The second list to combine, or None.

#     Returns:
#         list: A new list containing all elements from both input lists.
#                If an input is None, it's treated as an empty list.
#     """
#     if not left:
#         left = []
#     if not right:
#         right = []
#     return left + right


# class CustomReducerState(TypedDict):
#     foo: Annotated[list[int], reduce_list]


# def node_1(state):
#     print("---Node 1---")
#     return {"foo": [2]}


# # Build graph
# builder_3 = StateGraph(CustomReducerState)
# builder_3.add_node("node_1", node_1)

# # Logic
# builder_3.add_edge(START, "node_1")
# builder_3.add_edge("node_1", END)

# # Add
# graph = builder_3.compile()

# try:
#     print(graph.invoke({"foo": None}))
# except TypeError as e:
#     print(f"TypeError occurred: {e}")


"""Messages
In module 1, we showed how to use a built-in reducer, add_messages, to handle messages in state.

We also showed that MessagesState is a useful shortcut if you want to work with messages.

MessagesState has a built-in messages key
It also has a built-in add_messages reducer for this key
These two are equivalent.

We'll use the MessagesState class via from langgraph.graph import MessagesState for brevity."""

from langgraph.graph import MessagesState
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage
from langgraph.graph.message import add_messages


# Use MessagesState, which includes the messages key with add_messages reducer
class ExtendedMessagesState(MessagesState):
    added_key_1: str
    added_key_2: str


initial_messages = [
    AIMessage(content="Hello! How can I assist you?", name="Model"),
    HumanMessage(
        content="I'm looking for information on marine biology.", name="Lance"
    ),
]

new_message = AIMessage(
    content="Sure, I can help with that. What specifically are you interested in?",
    name="Model",
)

print(add_messages(initial_messages, new_message))


"""Re-writing
Let's show some useful tricks when working with the add_messages reducer.

If we pass a message with the same ID as an existing one in our messages list, it will get overwritten!"""

# Initial state
initial_messages = [
    AIMessage(content="Hello! How can I assist you?", name="Model", id="1"),
    HumanMessage(
        content="I'm looking for information on marine biology.", name="Lance", id="2"
    ),
]

# New message to add
new_message = HumanMessage(
    content="I'm looking for information on whales, specifically", name="Lance", id="2"
)

# Test
print(add_messages(initial_messages, new_message))

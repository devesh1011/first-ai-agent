"""let's first talk a bit more about advanced ways to work with messages in graph state."""

from pprint import pprint
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph import StateGraph, START, END
import os
from dotenv import load_dotenv
from langchain_core.messages import RemoveMessage, trim_messages

load_dotenv()

messages = [AIMessage(f"So you said you were researching ocean mammals?", name="Bot")]
messages.append(
    HumanMessage(
        f"Yes, I know about whales. But what others should I learn about?", name="Lance"
    )
)

# for m in messages:
#     m.pretty_print()

llm = ChatOpenAI(model="gpt-4o", api_key=os.environ.get("OPENAI_API_KEY"))
# llm.invoke(messages)


def chat_model_node(state: MessagesState):
    return {"messages": llm.invoke(state["messages"])}


# Build graph
builder = StateGraph(MessagesState)
builder.add_node("chat_model", chat_model_node)
builder.add_edge(START, "chat_model")
builder.add_edge("chat_model", END)
graph = builder.compile()

# output = graph.invoke({"messages": messages})
# for m in output["messages"]:
#     m.pretty_print()

"""A practical challenge when working with messages is managing long-running conversations.

Long-running conversations result in high token usage and latency if we are not careful, because we pass a growing list of messages to the model."""


def filter_messages(state: MessagesState):
    # Delete all but the 2 most recent messages
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    return {"messages": delete_messages}


builder2 = StateGraph(MessagesState)
builder2.add_node("filter", filter_messages)
builder2.add_node("chat_model", chat_model_node)
builder2.add_edge(START, "filter")
builder2.add_edge("filter", "chat_model")
builder2.add_edge("chat_model", END)
graph = builder2.compile()

# Message list with a preamble
messages = [AIMessage("Hi.", name="Bot", id="1")]
messages.append(HumanMessage("Hi.", name="Lance", id="2"))
messages.append(
    AIMessage("So you said you were researching ocean mammals?", name="Bot", id="3")
)
messages.append(
    HumanMessage(
        "Yes, I know about whales. But what others should I learn about?",
        name="Lance",
        id="4",
    )
)

# # Invoke
filtered_output = graph.invoke({"messages": messages})
# for m in filtered_output["messages"]:
#     m.pretty_print()


"""Filtering messages
If you don't need or want to modify the graph state, you can just filter the messages you pass to the chat model."""


# Node
def chat_model_node_2(state: MessagesState):
    return {"messages": [llm.invoke(state["messages"][-1:])]}


# Build graph
builder = StateGraph(MessagesState)
builder.add_node("chat_model", chat_model_node_2)
builder.add_edge(START, "chat_model")
builder.add_edge("chat_model", END)
graph = builder.compile()

messages.append(filtered_output["messages"][-1])
messages.append(HumanMessage(f"Tell me more about Narwhals!", name="Lance"))

# Invoke, using message filtering
output = graph.invoke({"messages": messages})
# for m in output["messages"]:
#     m.pretty_print()


"""Trim messages
Another approach is to trim messages, based upon a set number of tokens.

This restricts the message history to a specified number of tokens.

While filtering only returns a post-hoc subset of the messages between agents, trimming restricts the number of tokens that a chat model can use to respond."""


def chat_model_node_3(state: MessagesState):
    messages = trim_messages(
        state["messages"],
        max_tokens=100,
        strategy="last",
        token_counter=ChatOpenAI(model="gpt-4o"),
        allow_partial=True,
    )
    return {"messages": [llm.invoke("messages")]}


# Build graph
builder_3 = StateGraph(MessagesState)
builder_3.add_node("chat_model", chat_model_node)
builder_3.add_edge(START, "chat_model")
builder_3.add_edge("chat_model", END)
graph = builder_3.compile()

messages.append(output["messages"][-1])
messages.append(HumanMessage(f"Tell me where Orcas live!", name="Lance"))

messages_out_trim = graph.invoke({"messages": messages})

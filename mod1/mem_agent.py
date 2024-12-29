"""Now, we're going extend our agent by introducing memory."""

from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import tools_condition
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

memory = MemorySaver()


def multiply(a: int, b: int) -> int:
    """Multiply a and b.

    Args:
        a: first int
        b: second int
    """
    return a * b


# This will be a tool
def add(a: int, b: int) -> int:
    """Adds a and b.

    Args:
        a: first int
        b: second int
    """
    return a + b


def divide(a: int, b: int) -> float:
    """Divide a and b.

    Args:
        a: first int
        b: second int
    """
    return a / b


tools = [add, multiply, divide]
llm = ChatOpenAI(
    model="gpt-4o", temperature=0.1, api_key=os.environ.get("OPENAI_API_KEY")
)

llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)

sys_msg = SystemMessage(
    content="You are a helpful assistant tasked with performing arithmeticon a set of inputs."
)


def assistant(state: MessagesState):
    return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}


builder = StateGraph(MessagesState)

builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant",
    tools_condition,
)

builder.add_edge("tools", "assistant")

"""LangGraph can use a checkpointer to automatically save the graph state after each step.

This built-in persistence layer gives us memory, allowing LangGraph to pick up from the last state update.

One of the easiest checkpointers to use is the MemorySaver, an in-memory key-value store for Graph state.

All we need to do is simply compile the graph with a checkpointer, and our graph has memory!"""

react_graph = builder.compile(checkpointer=memory)

"""When we use memory, we need to specify a thread_id.

This thread_id will store our collection of graph states.

Here is a cartoon:

The checkpointer write the state at every step of the graph
These checkpoints are saved in a thread
We can access that thread in the future using the thread_id"""

config = {"configurable": {"thread_id": "1"}}

messages = [HumanMessage(content="Add 3 and 4.")]

messages = react_graph.invoke({"messages": messages}, config)
for m in messages["messages"]:
    m.pretty_print()

messages = [HumanMessage(content="Multiply that by 2.")]
messages = react_graph.invoke({"messages": messages}, config)
for m in messages["messages"]:
    m.pretty_print()

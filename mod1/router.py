"""(1) Add a node that will call our tool.

(2) Add a conditional edge that will look at the chat model model output, and route to our tool calling node or simply end if no tool call is performed."""

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition
import os
from dotenv import load_dotenv

load_dotenv()


def multiply(a: int, b: int) -> int:
    """Multiply a and b.

    Args:
        a: first int
        b: second int
    """
    return a * b


llm = ChatOpenAI(model="gpt-4o", api_key=os.environ.get("OPENAI_API_KEY"))
llm_with_tools = llm.bind_tools([multiply])


"""We use the built-in ToolNode and simply pass a list of our tools to initialize it.

We use the built-in tools_condition as our conditional edge."""


def tool_calling_llm(state: MessagesState):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


# build graph
builder = StateGraph(MessagesState)
builder.add_node("tool_calling_llm", tool_calling_llm)
builder.add_node("tools", ToolNode([multiply]))
builder.add_edge(START, "tool_calling_llm")
builder.add_conditional_edges("tool_calling_llm", tools_condition)

builder.add_edge("tools", END)

graph = builder.compile()

from langchain_core.messages import HumanMessage

messages = [HumanMessage(content="Multiply 4 and 5.")]
messages = graph.invoke({"messages": messages})
for m in messages["messages"]:
    m.pretty_print()

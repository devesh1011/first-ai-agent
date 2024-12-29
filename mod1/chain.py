from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
import os
from dotenv import load_dotenv
from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END

# Load environment variables
load_dotenv()

# Initialize the LLM
llm = ChatOpenAI(
    model="gpt-4o", temperature=0.1, api_key=os.environ.get("OPENAI_API_KEY")
)


# Define a tool (example: multiply function)
def multiply(a: int, b: int) -> int:
    return a * b


# Bind tools to the LLM
llm_with_tools = llm.bind_tools([multiply])

# Test the LLM with tools
print(
    llm_with_tools.invoke(
        [HumanMessage(content="What is 2 multiplied by 3?", name="Lance")]
    )
)


# Define the state for the graph
class MessagesState(TypedDict):
    messages: Annotated[list, add_messages]


# Initialize the graph builder
builder = StateGraph(MessagesState)


# Define a function to call the LLM with tools
def call_llm_with_tools(state: MessagesState):
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


# Add the LLM node to the graph
builder.add_node("tool_calling_llm", call_llm_with_tools)

# Add edges to the graph
builder.add_edge(START, "tool_calling_llm")
builder.add_edge("tool_calling_llm", END)

# Compile the graph
graph = builder.compile()

# Invoke the graph with the correct input format
messages = graph.invoke({"messages": [HumanMessage(content="Hello!")]})

# Print the output messages
for m in messages["messages"]:
    m.pretty_print()

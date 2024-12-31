"""Rather than just trimming or filtering messages, we'll show how to use LLMs to produce a running summary of the conversation.

This allows us to retain a compressed representation of the full conversation, rather than just removing it with trimming or filtering.
"""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langgraph.checkpoint.memory import MemorySaver
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the LLM
model = ChatOpenAI(model="gpt-4o", api_key=os.environ.get("OPENAI_API_KEY"))


# Define the state for the graph
class State(MessagesState):
    summary: str  # Field to store the running summary


# Function to call the LLM for generating responses
def call_model(state: State):
    summary = state.get("summary", "")
    if summary:
        # Prepend the summary as context for the LLM
        system_msg = f"Summary of conversation earlier: {summary}"
        msgs = [SystemMessage(content=system_msg)] + state["messages"]
    else:
        msgs = state["messages"]
    # Generate a response from the LLM
    response = model.invoke(msgs)
    # Append the AI's response to the messages list
    return {"messages": state["messages"] + [response]}


# Function to summarize the conversation
def conv_summary(state: State):
    summary = state.get("summary", "")
    if summary:
        # Extend the existing summary
        summary_msg = (
            f"This is the summary of the conversation to date: {summary}\n\n"
            "Extend the summary by taking into account the new messages above:"
        )
    else:
        # Create a new summary
        summary_msg = "Create a summary of the conversation above:"
    # Generate the summary using the LLM
    msgs = state["messages"] + [HumanMessage(content=summary_msg)]
    response = model.invoke(msgs)
    return {"summary": response.content, "messages": []}


# Function to decide whether to continue or summarize
def should_continue(state: State):
    msgs = state["messages"]
    if len(msgs) > 6:  # Summarize if more than 6 messages
        return "summarize_conversation"
    return END


# Define the graph
workflow = StateGraph(State)
workflow.add_node("conversation", call_model)  # Node for regular conversation
workflow.add_node("summarize_conversation", conv_summary)  # Node for summarization
workflow.add_edge(START, "conversation")  # Start with the conversation node
workflow.add_conditional_edges(
    "conversation", should_continue
)  # Decide to summarize or end
workflow.add_edge("summarize_conversation", END)  # End after summarization

# Compile the graph with memory checkpointing
memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)

# Configuration for the conversation thread
config = {"configurable": {"thread_id": "1"}}

# Continuous conversation loop
print("Welcome to the AI conversation! Type 'exit' to end the conversation.")
while True:
    # Get user input
    user_input = input("You: ")
    if user_input.lower() == "exit":
        print("Goodbye!")
        break

    # Invoke the graph with the user's input
    output = graph.invoke({"messages": [HumanMessage(content=user_input)]}, config)

    # Print the AI's response
    for message in output["messages"][-1:]:  # Only print the latest response
        print(f"AI: {message.content}")

    # Print the summary if it exists
    if "summary" in output and output["summary"]:
        print("\n--- Conversation Summary ---")
        print(output["summary"])
        print("----------------------------\n")

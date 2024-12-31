from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain.tools import tool
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4", api_key=os.getenv("OPENAI_API_KEY"))


# Define a tool to fetch weather data
@tool
def fetch_weather(city: str) -> dict:
    """Fetch the current weather data for a given city."""
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()  # Return raw weather data
    else:
        return {"error": f"Could not fetch weather data for {city}."}


# Bind tools to the LLM
llm_with_tools = llm.bind_tools([fetch_weather])


# Define the state
class State:
    messages: list  # Stores the conversation history


# Function to call the LLM and handle tool usage
def agent(state: State):
    # Extract the conversation history
    messages = state["messages"]
    # Call the LLM with the conversation history
    response = llm_with_tools.invoke(messages)
    # Check if the LLM wants to use a tool
    if hasattr(response, "tool_calls") and response.tool_calls:
        tool_name = response.tool_calls[0]["name"]
        tool_input = response.tool_calls[0]["args"]
        if tool_name == "fetch_weather":
            # Call the weather tool
            weather_data = fetch_weather(tool_input["city"])
            # Pass the raw weather data back to the LLM to generate a response
            llm_response = llm.invoke(
                [
                    *messages,
                    AIMessage(content=f"Weather data: {weather_data}"),
                    HumanMessage(
                        content="Generate a user-friendly response based on the weather data."
                    ),
                ]
            )
            # Append the LLM's response to the conversation history
            return {"messages": messages + [llm_response]}
    # If no tool is called, append the LLM's response
    return {"messages": messages + [response]}


# Define the graph
workflow = StateGraph(State)
workflow.add_node("agent", agent)


workflow.add_edge(START, "agent")
workflow.add_edge("agent", END)
graph = workflow.compile()

# Run the agent
output = graph.invoke(
    {"messages": [HumanMessage(content="What's the weather in New York?")]}
)
print(output["messages"][-1].content)

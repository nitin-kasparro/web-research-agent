from google.adk.agents.llm_agent import Agent


from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event

# Mock tool implementation
def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city."""
    return {"status": "success", "city": city, "time": "10:30 AM"}

def get_weather_report(city:str) -> dict:
    """Returns the current weather in a specified city."""
    return {
        "status":"success",
        "city":city,
        "weather":"sunny"
        
    }

root_agent = Agent(
    model='gemini-3.6-flash',
    name='root_agent',
    description="Tells the current time in a specified city.",
    instruction="You are a helpful assistant that tells the current time in cities. Use the 'get_current_time' tool for this purpose.",
    tools=[get_current_time,get_weather_report],
)

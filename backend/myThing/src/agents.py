# This file defines agents and their associated functions

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from agenttools import *
from prompts import detect_prompt
import ollama

default_model_type: str = "llama3" # "gemini-3-flash" # Depends
default_model_provider: str = "ollama" 
model_prompts = {
    "detect": detect_prompt(),
    "abstract": '''Rewrite the text to abstract the protected information, without changing other parts. For example:
    Input: <Text>I graduated from CMU, and I earn a six-figure salary. Today in the office...</Text>
    <ProtectedInformation>CMU, Today</ProtectedInformation>
    Output JSON: {"results": [{"protected": "CMU", "abstracted":"a prestigious university"}, {"protected": "Today", "abstracted":"Recently"}}] Please use "results" as the main key in the JSON object.
    ''', 
    "simple": '''''',
    "decider":'''Input is JSON with current_text and results (detected PII list). For each item in results, choose action: redact or abstract. Prefer privacy first, but keep task usefulness. Return JSON only: {"results":[{"pii":"...","action":"redact|abstract","reason":"short reason"}]}''', 
    "optimizer":'''Given decider prompts with scores, generate one improved decider prompt that should score higher on privacy and utility balance. Return JSON only: {"results":[{"optimized_prompt":"...","why":"short explanation"}]}''',
    "scorer":'''Score each candidate using promptid, suggested prompt, user prompt, and model output for privacy protection and task usefulness. Return JSON only: {"results":[{"promptid":"...","score":0.0}]} with score 0.0-100.0.'''
}

class CustomState(AgentState):
    original_message: str = ""
    detected_pii: list = []
    current_message: str = ""

class CustomMiddleware(AgentMiddleware):
    state_schema = CustomState
    tools = [] # Add tools, probably using a @wrap_tool_call
    # Include @dynamic_prompt tool if debugging mode is on

base_llm = init_chat_model(
    default_model_type, 
    model_provider=default_model_provider,
    temperature=0,
    model_kwargs={"format": "json"} # Doesn't actually help structure the output
)

# Create agents on fixed list, later to be replaced by model_prompts.keys
all_agents = {}
for agent_name in ["simple", "detect", "abstract", "decider", "scorer"]:
    all_agents[agent_name] = create_agent(
        base_llm,
        system_prompt=model_prompts.get(agent_name, ""),
        tools=None, #Will add tools later
        name=agent_name
    )


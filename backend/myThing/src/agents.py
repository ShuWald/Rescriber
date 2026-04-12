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
    "simple": ''''''
}

class CustomState(AgentState):
    original_message: str = ""
    detected_pii: list = []
    current_message: str = ""

class CustomMiddleware(AgentMiddleware):
    state_schema = CustomState
    tools = [] # Add tools, probably using a @wrap_tool_call
    # Include @dynamic_prompt tool if debugging mode is on

base_llm = init_chat_model(default_model_type, model_provider=default_model_provider)

#loop agents through models dict? or just define noramlly
agent = create_agent(
    base_llm,
    system_prompt=model_prompts.get("simple", ""),
    tools=None, #Will add tools later
    name="simple"
) 

all_agents = {}
all_agents["simple"] = agent


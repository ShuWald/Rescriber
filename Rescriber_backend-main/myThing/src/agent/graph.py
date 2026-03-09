from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from langgraph.graph import StateGraph
from langgraph.runtime import Runtime
from typing_extensions import TypedDict

import ollama

class Context(TypedDict):
    """
    See: https://langchain-ai.github.io/langgraph/cloud/how-tos/configuration_cloud/
    """

    model_name = "llama3"
    base_options = {"format": "json", "temperature": 0}
    system_prompts = {
        "detect": '''You an expert in cybersecurity and data privacy. You are now tasked to detect PII from the given text, using the following taxonomy only:

    ADDRESS
    IP_ADDRESS
    URL
    SSN
    PHONE_NUMBER
    EMAIL
    DRIVERS_LICENSE
    PASSPORT_NUMBER
    TAXPAYER_IDENTIFICATION_NUMBER
    ID_NUMBER
    NAME
    USERNAME
    
    KEYS: Passwords, passkeys, API keys, encryption keys, and any other form of security keys.
    GEOLOCATION: Places and locations, such as cities, provinces, countries, international regions, or named infrastructures (bus stops, bridges, etc.). 
    AFFILIATION: Names of organizations, such as public and private companies, schools, universities, public institutions, prisons, healthcare institutions, non-governmental organizations, churches, etc. 
    DEMOGRAPHIC_ATTRIBUTE: Demographic attributes of a person, such as native language, descent, heritage, ethnicity, nationality, religious or political group, birthmarks, ages, sexual orientation, gender and sex. 
    TIME: Description of a specific date, time, or duration. 
    HEALTH_INFORMATION: Details concerning an individual's health status, medical conditions, treatment records, and health insurance information. 
    FINANCIAL_INFORMATION: Financial details such as bank account numbers, credit card numbers, investment records, salary information, and other financial statuses or activities. 
    EDUCATIONAL_RECORD: Educational background details, including academic records, transcripts, degrees, and certification.
        
        For the given message that a user sends to a chatbot, identify all the personally identifiable information using the above taxonomy only, and the entity_type should be selected from the all-caps categories.
        Note that the information should be related to a real person not in a public context, but okay if not uniquely identifiable.
        Result should be in its minimum possible unit.
        Return me ONLY a json in the following format: {"results": [{"entity_type": YOU_DECIDE_THE_PII_TYPE, "text": PART_OF_MESSAGE_YOU_IDENTIFIED_AS_PII]}''',
        "abstract": '''Rewrite the text to abstract the protected information, without changing other parts. For example:
            Input: <Text>I graduated from CMU, and I earn a six-figure salary. Today in the office...</Text>
            <ProtectedInformation>CMU, Today</ProtectedInformation>
            Output JSON: {"results": [{"protected": "CMU", "abstracted":"a prestigious university"}, {"protected": "Today", "abstracted":"Recently"}}] Please use "results" as the main key in the JSON object.'''
    }


@dataclass
class State:
    """
    See: https://langchain-ai.github.io/langgraph/concepts/low_level/#state
    """

    changeme: str = "example"
    originalmessage: str = ""
    currentmessage: str = ""
    redactiondict: str = "" # dict not allowed???

async def get_input(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    #state.originalmessage = ? connect to frontend
    return {
        "message": "Hello world"
    }

async def call_model(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    
    #Maybe put this into another file and call whenever model is needed
    response = ollama.chat(
        model=runtime.context.get("model_name"),
        messages=[
            {'role': 'system', 'content': runtime.context.get("system_prompts", {}).get("detect")},
            {'role': 'user', 'content': state.originalmessage}
        ],
        format="json",
        stream=True,
        options=runtime.context.get("model_options")
    )

    return {
        "response": response,
        "changeme": "output from call_model. "
        f"Configured with {(runtime.context or {}).get('some_guy')}"
    }

async def interpret_and_send(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    #response -> redactiondict
    #send to user
    #streaming response?
    pass

async def get_user_choice(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    #chosen word, abstraction vs redaction
    pass

async def redact(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    #apply redactiondict to originalmessage -> currentmessage
    pass
async def abstract(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    #call model for abstracting selected content -> currentmessage
    pass


graph = (
    StateGraph(State, context_schema=Context)
    .add_node(get_input)
    .add_node(call_model)
    .add_node(interpret_and_send)
    .add_node(get_user_choice)
    .add_node(redact)
    .add_node(abstract)
    .add_edge("__start__", "get_input")
    .add_edge("get_input", "call_model")
    .add_edge("call_model", "interpret_and_send")
    .add_edge("interpret_and_send", "get_user_choice")
    .add_edge("get_user_choice", "redact")
    .add_edge("get_user_choice", "abstract")
    .compile(name="New Graph")
)

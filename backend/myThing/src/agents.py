from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langchain.agents import create_agent
from alltools import *
import ollama

model_type: str = "gemini-3-flash" # Provide ollama option with llama3 model
model_prompts = {
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
    Return me ONLY a json in the following format: {"results": [{"entity_type": YOU_DECIDE_THE_PII_TYPE, "text": PART_OF_MESSAGE_YOU_IDENTIFIED_AS_PII]}
    ''',
    "abstract": '''Rewrite the text to abstract the protected information, without changing other parts. For example:
    Input: <Text>I graduated from CMU, and I earn a six-figure salary. Today in the office...</Text>
    <ProtectedInformation>CMU, Today</ProtectedInformation>
    Output JSON: {"results": [{"protected": "CMU", "abstracted":"a prestigious university"}, {"protected": "Today", "abstracted":"Recently"}}] Please use "results" as the main key in the JSON object.
    '''
}

class CustomState(AgentState):
    original_message: str = ""
    detected_pii: list = []
    current_message: str = ""

class CustomMiddleware(AgentMiddleware):
    state_schema = CustomState
    tools = [] # Add tools, probably using a @wrap_tool_call
    # Include @dynamic_prompt tool if debugging mode is on

#loop agents through models dict? or just define noramlly
agent = create_agent(
    model_type, 
    name = "?",
    temperature = 0, 
    tools=None #Will add tools later
) 

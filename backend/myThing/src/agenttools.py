# This file defines agent tools and other helper functions

from langchain.agents.middleware import wrap_model_call, dynamic_prompt, ModelRequest, ModelResponse

@wrap_model_call
def checkerrorthing():
    pass

@dynamic_prompt
def saysomethingfordebugging():
    pass
# Overview of File Roles

`agents.py`
\- agent definitions, state, middleware, assign prompt
    \- state to remember information on pii obscuring process, useful for more granular control
    \- middleware contains model tools and functions for smarter behavior
\- reads model prompts from `prompts.py`
\- agent storage in `all_agents` dict

`prompts.py`
\- determines detect model prompt
\- todo: automatic reading from OPRO output file for best prompt

`agenttools.py`
\- defines agent tools

`working.py`
\- instantiate agents from `agents.py`
    \- distinguish between local and online models
\- initialize server
\- stream model outputs to client

`serverfunctions.py`
\- specifically flask-related functions helping `working.py`
\- flexibly sets handlers for routes corresponding to agents
\- \detect route also redirects to \simple under specific conditions

`agenthelpers.py`
\- functions relating to agent communication
    \- surrounding functionality for invoking agents
    \- parsing outputs to specific JSON structure

`loggingfunctions.py`
\- set and log files, by default into the Log directory



# Bonus Logic

1\. detectmodel should output an annotated usermessage (lets call it modifiedmessage) to better identify PII in user prompts. This is more accurate than the current approach of replacing all matching terms in entire query, which can redact unintended text, a major concern for longer queries. 
Possible approaches:
\- usermessage is annotated with special markers to signal PPI for quicker identification. (What if markers replicated by user?)
\- model returns indexes of PII in question (Prone to LLM errors?)

2\. Action decider model: Weighs the importance of found PIIs in message context, uses this to decide the best course of action for them
\- Includes message streaming

3\. Scorer: Scores the outputs of the action decider model based on effectiveness
\- Additional tools for logging prompts, outputs, scores into text files for further evaluation
\- Optimized prompting model: Creates self-feedback loop with action decider and scorer to find most optimal prompts
    \- Feedback loop uses aggregates to determine average scores for reliability

4\. Optimizer: Optimizes model prompts based on their scores
\- Access to large file relating to prompts and corresponding scores

5\. Issues
\- Inconsistent highlights issue? Frontend doesn't always pick up on outputs
    \- Likely due to current parser + non structured inputs
\- Timeout throws forntend disconnect error, persists?

6\. Other
\- Discontinuing client-side streaming requests? User input streaming is good for large-copy pasted blocks, but usually typing inputs combined with the constant clientside streaming causes multiple requests to models
    \- Cancel/discontinue older client requests when a newer one is sent, streaming of the request is still retained
\- Switch to OllamaChat for structured JSON outputs
\- Langchain State and Middleware for better control over inter-agentic communication (Current rerouting is inefficient and unnecessary, only implemented to preserve frontend code)
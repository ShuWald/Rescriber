# Helper functions for communication with agents 

import json


def extract_agent_text(agent_response):
    """Best-effort extraction of assistant text from agent response payloads."""
    if isinstance(agent_response, str):
        return agent_response

    if isinstance(agent_response, dict):
        messages = agent_response.get("messages")
        if isinstance(messages, list) and messages:
            last_message = messages[-1]
            content = getattr(last_message, "content", None)
            if content:
                return str(content)
        return json.dumps(agent_response, default=str)

    return str(agent_response)


def invoke_agent(agent, agent_name, message, logger=None):
    """Invoke a langchain-style agent and normalize result for API response."""
    try:
        raw = agent.invoke({"messages": [{"role": "user", "content": message}]})
    except Exception:
        # Fallback for agent implementations that accept plain text
        raw = agent.invoke(message)

    # Keep raw output visible for debugging before normalized extraction.
    raw_text = str(raw)
    print(f"[AGENT:{agent_name}] RAW: {raw_text}")
    if logger is not None:
        logger(f"[AGENT:{agent_name}] Raw response: {raw_text}")

    agent_text = extract_agent_text(raw)
    print(f"[AGENT:{agent_name}] EXTRACTED: {agent_text}")
    if logger is not None:
        logger(f"[AGENT:{agent_name}] Extracted response: {agent_text}")
    return [{"agent": agent_name, "text": agent_text}]

# Agent-specific helper functions.

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

    agent_text = extract_agent_text(raw)
    print(f"[AGENT:{agent_name}] {agent_text}")
    if logger is not None:
        logger(f"[AGENT:{agent_name}] Response: {agent_text}")
    return [{"agent": agent_name, "text": agent_text}]

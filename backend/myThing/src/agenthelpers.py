# Helper functions for communication with agents 

import json
import re


def _content_to_text(content):
    """Normalize message content payloads into plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text_value = item.get("text")
                if text_value is not None:
                    parts.append(str(text_value))
        return "".join(parts)
    if content is None:
        return ""
    return str(content)

# Extracts text from agent response payload
def extract_agent_text(agent_response):

    if isinstance(agent_response, str):
        return agent_response

    if isinstance(agent_response, dict):
        messages = agent_response.get("messages")
        if isinstance(messages, list) and messages:
            # Prefer assistant/AI message content when available.
            for message in reversed(messages):
                msg_type = type(message).__name__.lower()
                role = getattr(message, "role", None)
                content = getattr(message, "content", None)
                if content and ("ai" in msg_type or role == "assistant"):
                    return str(content)

            # Fallback to last message content if no assistant message was identified.
            last_message = messages[-1]
            content = getattr(last_message, "content", None)
            if content:
                return str(content)
        return json.dumps(agent_response, default=str)

    return str(agent_response)



# Extracts structured JSON from agent text responses
def extract_results_json(agent_text, agent_name, logger=None, fallback_on_failure=True):

    if isinstance(agent_text, dict):
        if "results" in agent_text:
            return agent_text
        warning_msg = f"[AGENT:{agent_name}] WARNING: Dict response missing 'results' key"
        if logger is not None:
            logger(warning_msg)
        return {"results": [{"agent": agent_name, "text": json.dumps(agent_text, default=str)}]}

    text = str(agent_text)

    # First try direct JSON parsing.
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict) and "results" in parsed:
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass

    # Next, try JSON code blocks (```json ... ``` or ``` ... ```).
    code_block_matches = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE)
    for block in code_block_matches:
        try:
            parsed = json.loads(block)
            if isinstance(parsed, dict) and "results" in parsed:
                return parsed
        except json.JSONDecodeError:
            continue

    # Then try to pull out the first JSON object from surrounding prose.
    match = re.search(r"\{[\s\S]*?\}", text)
    if match:
        # Try progressively larger objects starting at each '{'.
        starts = [m.start() for m in re.finditer(r"\{", text)]
        for start in starts:
            for end in range(len(text), start, -1):
                candidate = text[start:end].strip()
                if not candidate.endswith("}"):
                    continue
                try:
                    parsed = json.loads(candidate)
                    if isinstance(parsed, dict) and "results" in parsed:
                        return parsed
                except json.JSONDecodeError:
                    continue

    warning_msg = f"[AGENT:{agent_name}] WARNING: Could not extract structured JSON results"
    if logger is not None:
        logger(warning_msg)

    if not fallback_on_failure:
        return None

    return {"results": [{"agent": agent_name, "text": text}]}


# Invokes a langchain agent and extracts json results for response output
def invoke_agent(agent, agent_name, message, logger=None):

    raw = agent.invoke({"messages": [{"role": "user", "content": message}]})
    raw_text = str(raw)
    if logger is not None:
        logger(f"[AGENT:{agent_name}] Raw response: {raw_text}")

    # Extract text from response, currently for no purpose other than logging
    agent_text = extract_agent_text(raw)
    if logger is not None:
        logger(f"[AGENT:{agent_name}] Extracted text response: {agent_text}")

    return extract_results_json(agent_text, agent_name, logger=logger)


def invoke_agent_stream(agent, agent_name, message, logger=None):
    """Yield structured JSON snapshots from an agent stream as they become parseable."""

    emitted_signature = None
    accumulated_text = ""
    latest_text = ""

    def _emit_if_new(parsed_obj):
        nonlocal emitted_signature
        if not isinstance(parsed_obj, dict) or "results" not in parsed_obj:
            return None
        signature = json.dumps(parsed_obj, sort_keys=True, default=str)
        if signature == emitted_signature:
            return None
        emitted_signature = signature
        return parsed_obj

    try:
        stream_iter = agent.stream(
            {"messages": [{"role": "user", "content": message}]},
            stream_mode="updates",
        )
    except Exception as stream_error:
        if logger is not None:
            logger(f"[AGENT:{agent_name}] Stream setup failed, falling back to invoke: {type(stream_error).__name__}: {stream_error}")
        final_obj = invoke_agent(agent, agent_name, message, logger=logger)
        yield final_obj
        return

    for update in stream_iter:
        if not isinstance(update, dict):
            continue

        if logger is not None:
            logger(f"[AGENT:{agent_name}] Stream update: {update}")

        for node_payload in update.values():
            if not isinstance(node_payload, dict):
                continue

            messages = node_payload.get("messages")
            if not isinstance(messages, list) or not messages:
                continue

            latest_message = messages[-1]
            content = _content_to_text(getattr(latest_message, "content", None))
            if not content:
                continue

            msg_type = type(latest_message).__name__.lower()
            if "chunk" in msg_type:
                accumulated_text += content
                candidate_text = accumulated_text
            else:
                latest_text = content
                accumulated_text = content
                candidate_text = content

            parsed = extract_results_json(
                candidate_text,
                agent_name,
                logger=logger,
                fallback_on_failure=False,
            )
            maybe_emit = _emit_if_new(parsed)
            if maybe_emit is not None:
                yield maybe_emit

    final_text = latest_text or accumulated_text
    if final_text:
        final_obj = extract_results_json(final_text, agent_name, logger=logger)
    else:
        final_obj = {"results": []}

    maybe_emit_final = _emit_if_new(final_obj)
    if maybe_emit_final is not None:
        yield maybe_emit_final

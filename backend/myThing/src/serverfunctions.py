# Server routing and handler utilities.

import json
import threading
import requests
from flask import Response, jsonify, request
from agenthelpers import invoke_agent
from loggingfunctions import log_to_file

# Return one newline-delimited JSON object since trailing newline is required by frontend parser
def _ndjson_response(payload, status=200):
    response_line = json.dumps(payload, ensure_ascii=True) + "\n"
    return Response(response_line, status=status, mimetype="application/json")


# Stream NDJSON responses for an agent call and trigger reroutes as results are streamed
def handle_streaming_agent_response(agent_obj, name, msg):
    # Per-request trigger latch: simple fires once per request (prefix is static on original message)
    simple_triggered = [False]

    def _stream_generator():
        latest_response = None

        try:
            stream_iter = invoke_agent(
                agent_obj,
                name,
                msg,
                logger=lambda m, route_name=name: log_to_file(m, print_too=True, route=route_name),
                streaming=True,
            )

            for partial_response in stream_iter:
                latest_response = partial_response

                # Launch reroutes before yielding the chunk so the generator does not depend on a later resume
                # to reach the reroute code. This matters when the model emits only one update and then stops.
                if name == "detect":
                    # Simple: one-time trigger per request (prefix check on original message doesn't change across chunks)
                    if not simple_triggered[0]:
                        simple_thread = threading.Thread(target=simple_rerouteroutelogic, args=(msg,), daemon=True)
                        simple_thread.start()
                        simple_triggered[0] = True

                    # Decider: always fire on each chunk (independent of simple; stateless reroute)
                    log_to_file(
                        f"[DETECT->DECIDER] Streaming chunk observed; launching reroute with results={len(latest_response.get('results', [])) if isinstance(latest_response, dict) else 'n/a'}",
                        print_too=True,
                        route="detect",
                    )
                    decider_thread = threading.Thread(target=decider_rerouteroutelogic, args=(latest_response, msg), daemon=True)
                    decider_thread.start()

                if name == "decider":
                    # Abstract: always fire on each chunk; handler filtering already narrows the reroute candidates.
                    log_to_file(
                        f"[DECIDER->ABSTRACT] Streaming chunk observed; launching reroute with results={len(latest_response.get('results', [])) if isinstance(latest_response, dict) else 'n/a'}",
                        print_too=True,
                        route="decider",
                    )
                    abstract_thread = threading.Thread(target=abstract_rerouteroutelogic, args=(latest_response, msg), daemon=True)
                    abstract_thread.start()

                # Frontend stream parser expects newline-delimited JSON objects.
                # Keep the trailing '\n' so ondevice.js can flush a complete line immediately.
                yield json.dumps(partial_response, ensure_ascii=True) + "\n"
        except Exception as e:
            log_to_file(f"[AGENT:{name}] Stream failed: {type(e).__name__}: {e}", print_too=True, route=name)
            latest_response = invoke_agent(
                agent_obj,
                name,
                msg,
                logger=lambda m, route_name=name: log_to_file(m, print_too=True, route=route_name),
                streaming=False,
            )
            # Keep fallback payload in the same NDJSON shape the frontend already parses.
            yield json.dumps(latest_response, ensure_ascii=True) + "\n"

        if latest_response is None:
            latest_response = {"results": []}
            yield json.dumps(latest_response, ensure_ascii=True) + "\n"

        log_to_file(f"[AGENT:{name}] Final results: {latest_response}", print_too=True, route=name)

    return Response(_stream_generator(), status=200, mimetype="application/json")

# Background reroute to any route (threaded, non-blocking)
def reroute_to_route(route_name, message, base_url="https://localhost:5331", source_route="detect", timeout=45):

    target_url = f"{base_url.rstrip('/')}/{route_name.lstrip('/')}"
    payload = {"message": message}
    log_to_file(
        f"[REROUTE:{source_route}->{route_name}] Base reroute invoked",
        print_too=True,
        route=source_route,
    )
    log_to_file(
        f"[REROUTE:{source_route}->{route_name}] Posting to {target_url}",
        route=source_route,
    )

    try:
        target_response = requests.post(
            target_url,
            json=payload,
            verify=False,
            timeout=timeout,
        )
        response_text = target_response.text
        log_to_file(
            f"[REROUTE:{source_route}->{route_name}] Status code: {target_response.status_code}",
            print_too=True,
            route=source_route,
        )
        log_to_file(
            f"[REROUTE:{source_route}->{route_name}] Response: {response_text}",
            print_too=True,
            route=route_name,
        )
    except Exception as e:
        error_text = f"{type(e).__name__}: {e}"
        log_to_file(
            f"[REROUTE:{source_route}->{route_name}] FAILED: {error_text}",
            print_too=True,
            route=source_route,
        )


# Reroutes to simple when message starts with "Simple: ", for testing and demonstration purposes
def simple_rerouteroutelogic(message=None, base_url="https://localhost:5331"):

    simple_prefix = "Simple: "
    if not isinstance(message, str):
        message = str(message)
    if not message.startswith(simple_prefix):
        log_to_file("[DETECT->SIMPLE] Skipped: message does not start with 'Simple: '", print_too=True, route="detect")
        return

    simple_input = message[len(simple_prefix):].strip()
    log_to_file(f"[DETECT->SIMPLE] Prefix matched. Payload length={len(simple_input)}", route="detect")
    reroute_to_route("simple", simple_input, base_url=base_url, source_route="detect")


# For rerouting detect results to decider
def decider_rerouteroutelogic(detect_response, current_text, base_url="https://localhost:5331"):

    detect_results = []
    if isinstance(detect_response, dict):
        raw_results = detect_response.get("results", [])
        if isinstance(raw_results, list):
            detect_results = raw_results

    decider_payload = {
        "current_text": str(current_text),
        "results": detect_results,
    }
    try:
        message = json.dumps(decider_payload, ensure_ascii=True)
    except TypeError:
        log_to_file("[DETECT->DECIDER] WARNING: Failed to serialize decider payload to JSON, falling back to string", print_too=True, route="detect")
        message = str(decider_payload)

    log_to_file(
        f"[DETECT->DECIDER] Rerouting {len(detect_results)} detected item(s) with current_text to decider",
        print_too=True,
        route="detect",
    )
    reroute_to_route("decider", message, base_url=base_url, source_route="detect")


# For rerouting decider results to abstract
def abstract_rerouteroutelogic(decider_response, decider_input_message, base_url="https://localhost:5331"):

    log_to_file("[DECIDER->ABSTRACT] Evaluating abstract reroute payload", print_too=True, route="decider")

    current_text = ""
    try:
        decider_input = json.loads(decider_input_message) if isinstance(decider_input_message, str) else {}
        if isinstance(decider_input, dict):
            current_text = str(decider_input.get("current_text", "")).strip()
    except json.JSONDecodeError:
        current_text = ""

    if not current_text:
        log_to_file("[DECIDER->ABSTRACT] Skipped: current_text missing from decider payload", print_too=True, route="decider")
        return

    results = []
    if isinstance(decider_response, dict):
        raw_results = decider_response.get("results", [])
        if isinstance(raw_results, list):
            results = raw_results

    log_to_file(
        f"[DECIDER->ABSTRACT] Payload inspection: results={len(results)} current_text_length={len(current_text)}",
        print_too=True,
        route="decider",
    )

    protected_terms = []
    for item in results:
        if not isinstance(item, dict):
            continue
        action = str(item.get("action", "")).strip().lower()
        if action == "abstract":
            protected_value = item.get("pii") or item.get("protected") or item.get("text")
            if protected_value is not None:
                term = str(protected_value).strip()
                if term:
                    protected_terms.append(term)

    # De-duplicate while preserving order.
    protected_terms = list(dict.fromkeys(protected_terms))

    if not protected_terms:
        log_to_file("[DECIDER->ABSTRACT] Skipped: no items with action='abstract'", print_too=True, route="decider")
        return

    message = f"<Text>{current_text}</Text>\n<ProtectedInformation>{', '.join(protected_terms)}</ProtectedInformation>"

    log_to_file(
        f"[DECIDER->ABSTRACT] Rerouting text with {len(protected_terms)} abstract target(s) to abstract",
        print_too=True,
        route="decider",
    )
    reroute_to_route("abstract", message, base_url=base_url, source_route="decider")


# Flexibly defines POST routes based on a provided dictionary of agents
def initialize_agent_handlers(app, all_agents, enable_streaming=True):
    handlers = {}
    for agent_name, agent in all_agents.items():
        def _handler(msg, name=agent_name, agent_obj=agent):
            if enable_streaming:
                return handle_streaming_agent_response(agent_obj, name, msg)

            #Actual agent invocation
            response = invoke_agent(
                agent_obj,
                name,
                msg,
                logger=lambda m, route_name=name: log_to_file(m, print_too=True, route=route_name),
            )

            if name == "detect":
                # Fire off simple reroute in background thread (non-blocking) for logging only
                simple_thread = threading.Thread(target=simple_rerouteroutelogic, args=(msg,), daemon=True)
                simple_thread.start()

                # Fire off decider reroute in background thread (non-blocking) using detect output
                decider_thread = threading.Thread(target=decider_rerouteroutelogic, args=(response, msg), daemon=True)
                decider_thread.start()
                
            if name == "decider":
                # Fire off abstract reroute in background thread (non-blocking) using decider output
                abstract_thread = threading.Thread(target=abstract_rerouteroutelogic, args=(response, msg), daemon=True)
                abstract_thread.start()

            # response is now {"results": [...]} structure from invoke_agent
            log_to_file(f"[AGENT:{name}] Final results: {response}", print_too=True, route=name)

            payload = response if isinstance(response, dict) and "results" in response else {"results": response}
            # Convert all payloads(streaming/non-streaming) to Response objects containg NDJSON for consistency
            return _ndjson_response(payload)

        handlers[agent_name] = _handler
    
    # Register all routes dynamically
    define_post_routes(app, handlers)
    print(f"Initialized {len(handlers)} agent routes: {list(handlers.keys())}")
    for route in handlers:
        print(f"[ROUTES] Verified '/{route}' is mapped to the '{route}' agent handler")
        log_to_file(f"[ROUTES] Verified '/{route}' mapped to '{route}' handler", print_too=False, route=route)


# Review ondevice.js for how client calls server
# Posts the output of the function at the specified route, with streaming and timeout options
def post_function_output(
    function, #function that determines output, will probably be the model call function
    route="test",
    base_url="https://localhost:5331",
    streaming=False,
    timeout=60,
):
    url = f"{base_url.rstrip('/')}/{route.lstrip('/')}" # Prevents multiple slashes if base_url ends with / or route starts with /
    payload = {"message": function(route)} # assume route parameter necessary (model call will require route)
    response = requests.post(
        url,
        json=payload,
        stream=streaming,
        verify=False,
        timeout=timeout,
    )
    response.raise_for_status() # Raises an HTTPError if the response was unsuccessful (4xx or 5xx)

    if streaming:
        streamed_objects = []
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            try:
                streamed_objects.append(json.loads(line))
            except json.JSONDecodeError:
                streamed_objects.append({"raw": line})
        return streamed_objects
    return response.json()

# Flexibly defines POST routes based on a provided dictionary of route names and handler functions
# Each handler function should take the message as input and return the results to be sent back to the client.
def define_post_routes(app, handlers):

    # Defines behavior when POST request is made to /<route_name>
    # Current behavior: Extract and feed message to appropriate handler function, return results as JSON
    def _post_wrapper(route_name):
        data = request.get_json(silent=True) or {}
        message = data.get("message", "")
        log_to_file(f"[ROUTE] Incoming POST /{route_name}; has_message={bool(message)}", route=route_name)

        if not message:
            log_to_file(f"[ROUTE] Rejecting /{route_name}: no message", route=route_name)
            return _ndjson_response({"error": "No message provided"}, status=400)
        handler = handlers.get(route_name)
        if handler is None:
            log_to_file(f"[ROUTE] Unknown route /{route_name}", route=route_name)
            return _ndjson_response({"error": f"Unknown route: {route_name}"}, status=404)

        try:
            result = handler(message)
            log_to_file(f"[ROUTE] Completed /{route_name} successfully", route=route_name)

            if isinstance(result, Response):
                # Streaming handlers return Flask Response objects directly.
                # This is the final handoff to /<route_name> that the frontend consumes.
                return result

            payload = result if isinstance(result, dict) and "results" in result else {"results": result}
            # Non-stream fallback also uses the same NDJSON contract for consistency.
            return _ndjson_response(payload)
        except Exception as e:
            log_to_file(f"[ROUTE] Handler failed /{route_name}: {type(e).__name__}: {e}", route=route_name)
            return _ndjson_response({"error": f"Handler failed for /{route_name}", "details": str(e)}, status=500)

    app.add_url_rule(
        "/<route_name>",
        endpoint="flexible_post_route",
        view_func=_post_wrapper, 
        methods=["POST"],
    )


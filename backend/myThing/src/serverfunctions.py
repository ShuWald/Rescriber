# Server routing and handler utilities.

import requests
from flask import Response, jsonify, request
from agenthelpers import invoke_agent
from logging import log_to_file

#reroute to /simple when message begins with "Simple: "
def maybe_reroute_to_simple(message=None, base_url="https://localhost:5331"):

    simple_prefix = "Simple: "
    if message is None:
        data = request.get_json(silent=True) or {}
        message = data.get("message", "")

    if not isinstance(message, str):
        message = str(message)

    if not message.startswith(simple_prefix):
        log_to_file("[DETECT->SIMPLE] Skipped: message does not start with 'Simple: '", print_too=True, route="detect")
        return []

    simple_input = message[len(simple_prefix):].strip()
    simple_url = f"{base_url.rstrip('/')}/simple"
    simple_payload = {"message": simple_input}
    log_to_file(
        f"[DETECT->SIMPLE] Prefix matched. Posting to {simple_url} with payload length={len(simple_input)}",
        route="detect",
    )

    try:
        simple_response = requests.post(
            simple_url,
            json=simple_payload,
            verify=False,
            timeout=45,
        )
        log_to_file(f"[DETECT->SIMPLE] Status code: {simple_response.status_code}", print_too=True, route="detect")

        simple_json = simple_response.json()
        simple_results = simple_json.get("results", [])
        log_to_file(f"[DETECT->SIMPLE] Parsed result count: {len(simple_results)}", print_too=True, route="detect")
        log_to_file(f"[DETECT->SIMPLE] Final simple results: {simple_results}", print_too=True, route="detect")
        return simple_results

    except Exception as e:
        error_text = f"{type(e).__name__}: {e}"
        log_to_file(f"[DETECT->SIMPLE] FAILED: {error_text}", print_too=True, route="detect")
        return [{"agent": "simple", "error": error_text}]


# Flexibly defines POST routes based on a provided dictionary of agents
def initialize_agent_handlers(app, all_agents):
    handlers = {}
    for agent_name, agent in all_agents.items():
        def _handler(msg, name=agent_name, agent_obj=agent):
            results = invoke_agent(
                agent_obj,
                name,
                msg,
                logger=lambda m, route_name=name: log_to_file(m, print_too=True, route=route_name),
            )
            log_to_file(f"[AGENT:{name}] Final results: {results}", print_too=True, route=name)
            if name == "detect":
                results.extend(maybe_reroute_to_simple(msg))
                log_to_file(f"[AGENT:{name}] Results after simple reroute: {results}", print_too=True, route=name)
            return results

        handlers[agent_name] = _handler
    
    # Register all routes dynamically
    define_post_routes(app, handlers)
    print(f"Initialized {len(handlers)} agent routes: {list(handlers.keys())}")
    for route in handlers:
        print(f"[ROUTES] Verified '/{route}' is mapped to the '{route}' agent handler")
        log_to_file(f"[ROUTES] Verified '/{route}' mapped to '{route}' handler", print_too=False, route=route)


# Review ondevice.js for how client calls server
# Will also need response streaming later
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
        pass  # Handle streaming response as needed
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
            return jsonify({"error": "No message provided"}), 400
        handler = handlers.get(route_name)
        if handler is None:
            log_to_file(f"[ROUTE] Unknown route /{route_name}", route=route_name)
            return jsonify({"error": f"Unknown route: {route_name}"}), 404

        try:
            result = handler(message)
            log_to_file(f"[ROUTE] Completed /{route_name} successfully", route=route_name)
            return jsonify({"results": result}), 200
        except Exception as e:
            log_to_file(f"[ROUTE] Handler failed /{route_name}: {type(e).__name__}: {e}", route=route_name)
            return jsonify({"error": f"Handler failed for /{route_name}", "details": str(e)}), 500

    app.add_url_rule(
        "/<route_name>",
        endpoint="flexible_post_route",
        view_func=_post_wrapper, 
        methods=["POST"],
    )


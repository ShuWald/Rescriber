# Flask/backend server utility functions.

import time
import os  
import requests
from flask import Response, jsonify, request
from flask_cors import CORS
from agenthelpers import invoke_agent

default_log = "Log/default_log.txt"

def log_to_file(message, log_file=default_log):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "w") as f:
        f.write(message + "\n")
    return True

# Flexibly defines POST routes based on a provided dictionary of agents
def initialize_agent_handlers(app, all_agents):
    handlers = {}
    for agent_name, agent in all_agents.items():
        def _handler(msg, name=agent_name, agent_obj=agent):
            return invoke_agent(agent_obj, name, msg, logger=log_to_file)

        handlers[agent_name] = _handler
    
    # Register all routes dynamically
    define_post_routes(app, handlers)
    print(f"Initialized {len(handlers)} agent routes: {list(handlers.keys())}")
    if "simple" in handlers:
        print("[ROUTES] Verified '/simple' is mapped to the 'simple' agent handler")
        log_to_file("[ROUTES] Verified '/simple' mapped to 'simple' handler")


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
        log_to_file(f"[ROUTE] Incoming POST /{route_name}; has_message={bool(message)}")

        if not message:
            log_to_file(f"[ROUTE] Rejecting /{route_name}: no message")
            return jsonify({"error": "No message provided"}), 400
        handler = handlers.get(route_name)
        if handler is None:
            log_to_file(f"[ROUTE] Unknown route /{route_name}")
            return jsonify({"error": f"Unknown route: {route_name}"}), 404

        try:
            result = handler(message)
            log_to_file(f"[ROUTE] Completed /{route_name} successfully")
            return jsonify({"results": result}), 200
        except Exception as e:
            log_to_file(f"[ROUTE] Handler failed /{route_name}: {type(e).__name__}: {e}")
            return jsonify({"error": f"Handler failed for /{route_name}", "details": str(e)}), 500

    app.add_url_rule(
        "/<route_name>",
        endpoint="flexible_post_route",
        view_func=_post_wrapper, 
        methods=["POST"],
    )

# Defines behaviour for a basic test route
def basic_route_template(app):
    @app.route("/test", methods=["POST"])
    def test():
        data = request.get_json(silent=True) or {}
        input_text = data.get("message", "")
        if not input_text:
            return jsonify({"error": "No message provided"}), 400

        print("Test request received!")
        log_to_file("Test request received for /test")
        return jsonify({"results": [{"entity_type": "TEXT", "text": input_text}]}), 200


def test_functions():
    """Minimal test of all backend functions."""
    from flask import Flask
    
    # Create isolated test app so it doesn't lock the main app
    testapp = Flask(__name__)
    CORS(testapp)
    
    log_to_file("Test from test_functions")
    
    # Register all routes before making any requests, Flask locks after the first request is handled
    basic_route_template(testapp)
    define_post_routes(testapp, {"testroute": lambda m: [{"msg": m}]})
    
    client = testapp.test_client()
    payload = {"message": "test"}
    
    print(f"log_to_file: OK")
    # No more routes can be registered after the server handler starts from these requests
    print(f"basic_route_template (/test): {client.post('/test', json=payload).status_code}")
    print(f"define_post_routes (/testroute): {client.post('/testroute', json=payload).status_code}")
    
    # Test post_function_output (will error if server not running)
    try:
        post_function_output("msg", route="test", base_url="https://localhost:5331")
        print(f"post_function_output: OK")
    except Exception as e:
        print(f"post_function_output: {type(e).__name__}")


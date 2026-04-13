# Legacy server helper functions for reference and testing

import time

from flask import jsonify, request
from flask_cors import CORS

from logging import log_to_file
from serverfunctions import define_post_routes, post_function_output


# Defines behaviour for a basic test route
def basic_route_template(app):
    @app.route("/test", methods=["POST"])
    def test():
        data = request.get_json(silent=True) or {}
        input_text = data.get("message", "")
        if not input_text:
            return jsonify({"error": "No message provided"}), 400

        print("Test request received!")
        log_to_file("Test request received for /test", print_too=False, route="test")
        return jsonify({"results": [{"entity_type": "TEXT", "text": input_text}]}), 200


# Test all backend functions
def test_functions():
    from flask import Flask

    # Create isolated test app so it doesn't lock the main app
    testapp = Flask(__name__)
    CORS(testapp)

    test_message = "Test from test_functions"
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    log_to_file(f"[{current_time}] {test_message}", print_too=False, route="test")

    # Register all routes before making any requests, Flask locks after the first request is handled
    basic_route_template(testapp)
    define_post_routes(testapp, {"testroute": lambda m: [{"msg": m}]})

    client = testapp.test_client()
    payload = {"message": "test"}

    print("log_to_file: OK")
    print(f"basic_route_template (/test): {client.post('/test', json=payload).status_code}")
    print(f"define_post_routes (/testroute): {client.post('/testroute', json=payload).status_code}")

    # Test post_function_output (will error if server not running)
    try:
        post_function_output("msg", route="test", base_url="https://localhost:5331")
        print("post_function_output: OK")
    except Exception as e:
        print(f"post_function_output: {type(e).__name__}")

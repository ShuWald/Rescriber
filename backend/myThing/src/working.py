# This file instantiates agents, sets up the server, and streams responses to the client

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import time # Needed?
import threading
import os
import requests
from serverfunctions import * 
from agents import all_agents 


app = Flask(__name__)
CORS(app)


@app.route('/detect', methods=['POST'])
def detect():
    """Handler triggered when user finishes typing in ChatGPT."""
    data = request.get_json()
    input_text = data.get('message', '')
    
    if not input_text:
        return jsonify({"error": "No message provided"}), 400
    
    print(f"[DETECT] Message from user: {input_text}")
    log_to_file(f"Detect request: {input_text}")

    detect_results = [
        {"entity_type": "TEXT", "text": input_text}
    ]

    # Internal server-as-client POST to /simple.
    simple_url = "https://localhost:5331/simple"
    simple_payload = {"message": input_text}
    log_to_file(f"[DETECT->SIMPLE] Posting to {simple_url} with payload length={len(input_text)}")
    print(f"[DETECT->SIMPLE] Posting to {simple_url}")

    try:
        simple_response = requests.post(
            simple_url,
            json=simple_payload,
            verify=False,
            timeout=45,
        )
        log_to_file(f"[DETECT->SIMPLE] Status code: {simple_response.status_code}")
        print(f"[DETECT->SIMPLE] Status code: {simple_response.status_code}")

        simple_json = simple_response.json()
        simple_results = simple_json.get("results", [])
        log_to_file(f"[DETECT->SIMPLE] Parsed result count: {len(simple_results)}")
        print(f"[DETECT->SIMPLE] Parsed result count: {len(simple_results)}")

        detect_results.extend(simple_results)

    except Exception as e:
        error_text = f"{type(e).__name__}: {e}"
        log_to_file(f"[DETECT->SIMPLE] FAILED: {error_text}")
        print(f"[DETECT->SIMPLE] FAILED: {error_text}")
        detect_results.append({"agent": "simple", "error": error_text})
    
    return jsonify({
        "results": detect_results
    }), 200


if __name__ == "__main__":
    test_functions()
    initialize_agent_handlers(app, all_agents)
    
    cert_path = '../../python_cert/selfsigned.crt'
    key_path = '../../python_cert/selfsigned.key'
    
    try:
        print("\nStarting HTTPS server on port 5331...")
        app.run(
            host="0.0.0.0",
            port=5331,
            ssl_context=(cert_path, key_path),
            debug=False,
            threaded=True
        )
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

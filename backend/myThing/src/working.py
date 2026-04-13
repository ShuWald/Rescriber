# This file instantiates agents, sets up the server, and streams responses to the client

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import time # Needed?
import threading
import os
import requests
from logging import set_log
from serverfunctions import initialize_agent_handlers 
from legacyfunctions import test_functions
from agents import all_agents 

app = Flask(__name__)
CORS(app)

if __name__ == "__main__":
    set_log()
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

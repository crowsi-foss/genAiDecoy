from flask import Flask, request, jsonify
from collections import defaultdict
from genai_decoy.logging import ecs_log
import urllib.parse
import re
import asyncio

app = Flask(__name__)

# Store session context per client IP
sessions = defaultdict(list)


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
async def default(path):
    """Handles incoming HTTP requests and returns an AI-generated response."""

    # Extract and parse client certificate info from Traefik headers
    client_org, client_serial_nr = None, None
    x_forward_cert_info = request.headers.get('X-Forwarded-Tls-Client-Cert-Info')

    if x_forward_cert_info:
        try:
            unquoted_string = urllib.parse.unquote(x_forward_cert_info)
            org_match = re.search(r'O=([^";]+)', unquoted_string)
            serial_match = re.search(r'SerialNumber="([^"]+)"', unquoted_string)

            client_org = org_match.group(1) if org_match else None
            client_serial_nr = serial_match.group(1) if serial_match else None
        except Exception as e:
            ecs_log("error", "Failed to parse client certificate info", error=str(e))

    # Collect request data and identify client IP
    client_ip = request.headers.get('X-Real-IP', request.remote_addr)
    data = request.data.decode('utf-8')
    request_method = request.method
    request_path = request.path
    request_host = request.headers.get('Host')

    # Log incoming request with ECS-compliant field names
    ecs_log(
        "http_request",
        "Received HTTP request",
        http={"request": {"method": request_method}},
        url={"path": request_path},
        client={"ip": client_ip},
        host={"hostname": request_host},
        tls={
            "client": {
                "x509": {
                    "subject": {"organization": client_org},
                    "serial_number": client_serial_nr
                }
            }
        },
        body=data
    )

    # Update session context (keep only last 10 messages per client)
    sessions[client_ip].append(data)
    session_context = "\n".join(sessions[client_ip][-10:])

    # Prepare the context for the GenAI client
    context = f"{app.config['context']}\n{app.config['prompt']}\n{session_context}"
    try:
        # Ensure asynchronous call to AI client
        response = await app.config["genai_client"].generate_response(context)
        status_code = 200
    except Exception as e:
        ecs_log("error", "Failed to generate AI response", error=str(e))
        response = {"error": "Internal server error"}
        status_code = 500

    # Log the generated response with ECS-compliant fields
    ecs_log(
        "http_response",
        "Generated AI response",
        client={"ip": client_ip},
        http={"response": {"status_code": status_code}},
        body=response
    )

    return jsonify(response), status_code


def start_http_server(config, client):
    """Starts the HTTP server with the provided configuration."""
    app.config["genai_client"] = client
    app.config["prompt"] = config["prompt"]
    app.config["context"] = config["context"]

    # Run Flask app (note: Flask is inherently synchronous)
    app.run(host='0.0.0.0', port=config["port"])

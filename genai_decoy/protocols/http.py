from fastapi import FastAPI, Request
from collections import defaultdict
from genai_decoy.logging import ecs_log
import urllib.parse
import re
import asyncio

app = FastAPI()

# Store session context per client IP
sessions = defaultdict(list)


def extract_cert_info(x_forward_cert_info):
    """Extracts client certificate information from Traefik headers."""
    client_org = "None"
    client_serial_nr = "None"

    if x_forward_cert_info:
        unquoted_string = urllib.parse.unquote(x_forward_cert_info)

        organization_match = re.search(r'O=([^";]+)', unquoted_string)
        serial_number_match = re.search(r'SerialNumber="([^"]+)"', unquoted_string)

        client_org = organization_match.group(1) if organization_match else "None"
        client_serial_nr = serial_number_match.group(1) if serial_number_match else "None"

    return client_org, client_serial_nr




@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def handle_request(request: Request, full_path: str):
    """Handles incoming HTTP requests and returns an AI-generated response."""

    # Extract certificate info if provided
    client_org, client_serial_nr = extract_cert_info(request.headers.get("x-forwarded-tls-client-cert-info"))

    # Collect meta data for logging
    client_ip = request.headers.get("X-Real-IP", request.client.host)
    request_method = request.method
    request_path = full_path
    request_host = request.headers.get('Host')

    # Read request body
    body = await request.body()
    body_data = body.decode("utf-8") if body else ""

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
        body=body_data
    )

    # Update session context (keep only last 10 messages per client)
    sessions[client_ip].append(body_data)
    session_context = "\n".join(sessions[client_ip][-10:])

    # Prepare the context for the GenAI client
    context = f"{app.state.context}\n{app.state.prompt}\n{session_context}"

    try:
        # Ensure asynchronous call to AI client
        response = await app.state.genai_client.generate_response(context)
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

    return {"response": response}, status_code


async def start_http_server(config, client):
    """Starts the FastAPI HTTP server."""
    app.state.genai_client = client
    app.state.prompt = config["prompt"]
    app.state.context = config["context"]

    import uvicorn
    config = uvicorn.Config(app, host="0.0.0.0", port=config["port"], log_level="info")
    server = uvicorn.Server(config)

    await server.serve()
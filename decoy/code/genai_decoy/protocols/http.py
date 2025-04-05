from fastapi import FastAPI, Request
from collections import defaultdict, deque
from genai_decoy.logging import ecs_log
import urllib.parse
import re
from fastapi.responses import Response
import uvicorn

app = FastAPI()

# Initialize session with a default maxlen of 10
session = defaultdict(lambda: deque(maxlen=10))


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

    # Read request body
    body = await request.body()
    body_data = body.decode("utf-8") if body else ""

    # Collect meta data for logging
    client_ip = request.headers.get("X-Real-IP", request.client.host)

    # Serialisierung des Request-Objekts
    request_info = {
        "method": request.method,
        "url_path": request.url.path,
        "http_version": request.scope.get('http_version'),
        "query_string": request.scope.get('query_string').decode('utf-8'),
        "headers": dict(request.headers),
        "body_data": body_data
    }
    request_host = request.headers.get('Host')

    

    # Log incoming request with ECS-compliant field names
    ecs_log(
        "http_request",
        "Received HTTP request",
        http={"request": {"method": request_info["method"], "body":{"content":body_data}}, "referrer": request_info["url_path"]},
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
    )   

    
    # get the last requests of the client
    history = list(session[client_serial_nr])

    system_prompt = f"""{app.state.userprompt} Your response should be a valid http response. You are free to choose the status code and the body. Your response should be formatted like this your_status_code#####your_body. Make sure that your response doesn't contain ##### at any other place then where it is used for the seperation of the different parts of the response. The status code should be formatted as int. Your response body should be a json string."""
    

    try:
        # Ensure asynchronous call to AI client
        ai_response=await app.state.genai_client.generate_response(prompt=f"""Current received request: {request_info}\nLast received requests and given responses: {history}""", system_instructions=system_prompt)
        ai_status_code, ai_response_body = ai_response.split("#####")
        ai_status_code= int(ai_status_code)
    except Exception as e:
        ecs_log("error", "Failed to generate AI response", error=str(e))
        ai_response = {"error": "Internal server error"}
        ai_status_code = 500

    # Store the current request and response in the session
    session[client_serial_nr].append({
        "request": request_info,
        "response": {
            "status_code": ai_status_code,
            "body": ai_response_body
        }
    })

    # Log the generated response with ECS-compliant fields
    ecs_log(
        "http_response",
        "Generated AI response",
        http={"response": {"status_code": ai_status_code, "body": {"content": ai_response_body,} }},
        tls={
            "client": {
                "x509": {
                    "subject": {"organization": client_org},
                    "serial_number": client_serial_nr
                }
            }
        },
    ) 

    return Response(content=ai_response_body, status_code=ai_status_code, headers={"content_type": "application/json"})


async def start_http_server(config, client):
    """Starts the FastAPI HTTP server."""
    app.state.genai_client = client
    app.state.userprompt = f"""{config["baseprompt"]}\n{config["http"]["httpprompt"]}"""

    # Update session maxlen from config
    maxlen = config.get("userInputBuffering", 10)
    global session
    session = defaultdict(lambda: deque(maxlen=maxlen))

    
    config = uvicorn.Config(app, host="0.0.0.0", port=config["port"], log_level="info")
    server = uvicorn.Server(config)

    await server.serve()
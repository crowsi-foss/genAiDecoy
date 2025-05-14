import asyncio
import ssl
from genai_decoy.logging import ecs_log

# Global variable to store client certificate data, keyed by the outgoing port
client_certificate_data = {}

async def forward_data(source, destination):
    """
    Forward data between two streams (e.g., client and service).
    
    Reads data from the source stream and writes it to the destination stream.
    Handles exceptions and ensures the destination stream is closed properly.
    """
    try:
        while data := await source.read(1024):  # Read up to 1024 bytes from the source
            destination.write(data)  # Write the data to the destination
            await destination.drain()  # Ensure the data is sent
    except Exception as e:
        # Log any errors that occur during data forwarding
        ecs_log("error", "Data forwarding error", error=str(e))
    finally:
        # Close the destination stream to clean up resources
        destination.close()

async def handle_client(reader, writer, config):
    """
    Handle incoming client connections, verify mTLS, and forward data to the actual service.
    
    This function performs the following steps:
    1. Verifies the client's mTLS certificate.
    2. Establishes a connection to the internal service.
    3. Stores the client certificate data globally, keyed by the outgoing port.
    4. Forwards data bidirectionally between the client and the service.
    """
    try:
        # Extract the client's SSL certificate
        cert = writer.get_extra_info("peercert")
        if not cert:
            raise ssl.SSLError("No client certificate provided.")

        # Log the received client certificate
        ecs_log("info", "Client certificate received", certificate=cert)

        # Establish a connection to the internal service
        service_reader, service_writer = await asyncio.open_connection(
            "127.0.0.1", config["internalServicePort"]
        )

        # Store the client certificate data globally, keyed by the outgoing port
        global client_certificate_data
        outgoing_port = service_writer.get_extra_info("sockname")[1]  # Get the outgoing port
        client_certificate_data[outgoing_port] = cert  # Store the certificate data

        # Forward data bidirectionally between the client and the service
        await asyncio.gather(
            forward_data(reader, service_writer),  # Forward data from client to service
            forward_data(service_reader, writer)  # Forward data from service to client
        )
    except Exception as e:
        # Log any errors that occur during mTLS verification or data forwarding
        ecs_log("error", "mTLS verification or forwarding failed", error=str(e))
    finally:
        # Ensure the client connection is closed
        writer.close()
        await writer.wait_closed()

async def start_tcp_wrapper(config):
    """
    Start the TCP wrapper with mTLS verification.
    
    This function sets up an SSL context for mTLS, starts a TCP server, and listens for incoming connections.
    """
    # Create an SSL context for mTLS
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(
        certfile="/etc/ssl/certs/servertls/tls.crt",  # Server certificate
        keyfile="/etc/ssl/certs/servertls/tls.key"    # Server private key
    )
    ssl_context.load_verify_locations(cafile="/etc/ssl/certs/ca/ca.crt")  # CA certificate for client verification
    ssl_context.verify_mode = ssl.CERT_REQUIRED  # Require client certificates

    # Start the TCP server
    server = await asyncio.start_server(
        lambda r, w: handle_client(r, w, config),  # Handle incoming connections
        "0.0.0.0",  # Listen on all network interfaces
        config["port"],  # Port specified in the configuration
        ssl=ssl_context  # Use the SSL context for secure communication
    )

    # Log that the TCP wrapper has started
    ecs_log("info", "TCP wrapper started", port=config["port"])

    # Serve incoming connections indefinitely
    async with server:
        await server.serve_forever()

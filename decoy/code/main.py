import asyncio
import os
from genai_decoy.protocols.ssh import start_ssh_service
from genai_decoy.config import load_config, validate_config
from genai_decoy.genai_clients import get_genai_client
from genai_decoy.protocols.http import start_http_server
from genai_decoy.logging import ecs_log
from genai_decoy.tcp_wrapper import start_tcp_wrapper  # Import the TCP wrapper

async def main():
    config = load_config()    
    validate_config(config)

    ecs_log("startup", "Starting decoy service", protocol=config["protocol"], port=config["port"])

    client = get_genai_client(config)
    
    if config["protocol"] == "http":
        await start_http_server(config, client)
    elif config["protocol"] == "ssh":
        # Start the TCP wrapper for mTLS verification
        await asyncio.gather(
            start_tcp_wrapper(config),
            start_ssh_service(config, client)  # Start the SSH server on the internal port
        )
    else:
        ecs_log("error", "Protocol not supported", protocol=config["protocol"])
        raise NotImplementedError("Protocol not supported yet")

    await client.close()
    ecs_log("shutdown", "Decoy service stopped")

if __name__ == "__main__":
    asyncio.run(main())

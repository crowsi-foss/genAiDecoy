import asyncio
import asyncssh
import os
from genai_decoy.logging import ecs_log
from collections import defaultdict, deque
from typing import Optional

# Initialize session with a default maxlen of 10
client_session_history = defaultdict(lambda: deque(maxlen=10))

userprompt=""


class SSHServerSession(asyncssh.SSHServerSession):
    def __init__(self, config, aiclient):
        self._input_buffer = ""
        self._prompt = "RemoteConsole> "
        self.clientID = None
        self.config = config
        self.aiclient = aiclient

    def connection_made(self, chan):

        print("Connection made")
        self._chan = chan

        # Retrieve client IP from channel extra info
        peer_info = self._chan.get_extra_info("peername")
        self.clientID = peer_info[0] if peer_info and len(peer_info) > 0 else "unknown"

        # Initialize history for this IP if not already present
        global client_session_history
        if self.clientID not in client_session_history:
            client_session_history[self.clientID] = []

        self._chan.write(f"""{self.config["ssh"]["banner"]}\n""")
        self._chan.write(self._prompt)
        ecs_log("debug",f"SSH session established for {self.clientID}.")

    def shell_requested(self):
        ecs_log("info",f"SSH shell requested for {self.clientID}.")
        return True  # Accept interactive shell

    def data_received(self, data, datatype):
        ecs_log("debug",f"SSH data received from {self.clientID}: {data}")
        self._input_buffer += data
        if "\n" in self._input_buffer or "\r" in self._input_buffer:
            user_request = self._input_buffer.strip()
            self._input_buffer = ""
            ecs_log("info",f"SSH command received from {self.clientID}: {user_request}")
            asyncio.create_task(self.handle_command(user_request))

    async def handle_command(self, user_request: str):
        ecs_log("debug",f"Handling SSH command: {user_request}")

        system_prompt = f"""{userprompt} \nYour response should be a valid ssh response to the given command."""

        try:
            # Generate a response including the complete history as context
            response=await self.aiclient.generate_response(prompt=f"""Current received command: {user_request}\nLast received commands and given responses: {client_session_history[self.clientID]}""", system_instructions=system_prompt)
        except Exception as e:
            ecs_log("error", f"Failed to generate AI response. Error: {str(e)}")

        
        self._chan.write(response + "\r\n")
        self._chan.write(self._prompt)

        # Store the current request and response in the session
        client_session_history[self.clientID].append({
            "command": user_request,
            "response": response
        })

    def eof_received(self):
        return True

    def connection_lost(self, exc):
        ecs_log("info",f"SSH session terminated for {self.clientID}.")


class SSHServer(asyncssh.SSHServer):
    def __init__(self, config, aiclient):
        self.config = config
        self.aiclient = aiclient  
    

    def password_auth_supported(self):
        return True

    # def public_key_auth_supported(self):
    #     return True

    def validate_password(self, username, password):
        return True

    # def validate_public_key(self, username, key):
    #     return True

    def session_requested(self):
        print("Start Session ")
        return SSHServerSession(self.config, self.aiclient)
    
    def connection_lost(self, exc: Optional[Exception]) -> None:
        if exc:
            print('SSH connection error: ' + str(exc), file=sys.stderr)
        else:
            print('SSH connection closed.')

async def start_ssh_service(config, aiclient):
     # Update session maxlen from config
    maxlen = config.get("userInputBuffering", 10)
    global session
    session = defaultdict(lambda: deque(maxlen=maxlen))

    global userprompt
    userprompt = f"""{config["baseprompt"]}\n{config["ssh"]["sshprompt"]}"""

    # Path to the SSH host key file
    host_key_file = config["ssh"]["host_key_path"]
    if not os.path.exists(host_key_file):
        ecs_log("info","Generating new SSH host key for SSH service.")
        key = asyncssh.generate_private_key("ssh-rsa")
        with open(host_key_file, "wb") as f:
            f.write(key.export_private_key())
        os.chmod(host_key_file, 0o600)

    try:
        server = await asyncssh.create_server(
            lambda: SSHServer(config, aiclient),
            "0.0.0.0",
            config["port"],
            server_host_keys=[host_key_file],
            sftp_factory=None,
        )
        ecs_log("info","SSH service started")
        await server.wait_closed()
    except Exception as exc:
        ecs_log("error", f"Failed to start SSH service: {exc}")

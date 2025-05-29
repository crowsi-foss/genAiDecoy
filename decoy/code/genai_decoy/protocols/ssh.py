import asyncio
import asyncssh
import os
from genai_decoy.logging import ecs_log
from collections import defaultdict, deque
from typing import Optional

# Initialize session with a default maxlen of 10
client_session_history = defaultdict(lambda: deque(maxlen=10))

# global variable for user prompt
userprompt=""


class SSHServerSession(asyncssh.SSHServerSession):
    def __init__(self, config, aiclient):
        self._input_buffer = ""
        self._prompt = config["ssh"]["sshLinePrefix"]
        self.clientID = None
        self.config = config
        self.aiclient = aiclient

    def connection_made(self, chan):
        self._chan = chan

        # Retrieve client IP from channel extra info
        peer_info = self._chan.get_extra_info("peername")
        self.clientID = peer_info[0] if peer_info and len(peer_info) > 0 else "unknown"

        # Initialize history for this IP if not already present
        global client_session_history
        if self.clientID not in client_session_history:
            client_session_history[self.clientID] = []

        self._chan.write(f"""{self.config["ssh"]["banner"]}\r\n""")
        self._chan.write(self._prompt)
        ecs_log("info",f"SSH session established for {self.clientID}.")

    def shell_requested(self):
        ecs_log("info",f"SSH shell requested for {self.clientID}.")
        return True  # Accept interactive shell

    def data_received(self, data, datatype):
        # Log the received data from the client
        ecs_log("info", f"SSH data received from {self.clientID}: {data}")
        
        # Append the received data to the input buffer
        self._input_buffer += data
        
        # Check if the input buffer contains a newline or carriage return, indicating the end of a command
        if "\n" in self._input_buffer or "\r" in self._input_buffer:
            # Extract the complete user command by stripping whitespace
            user_request = self._input_buffer.strip()
            
            # Clear the input buffer for the next command
            self._input_buffer = ""
            
            # Handle the case where the user just hits enter
            if not user_request:
                self._chan.write("\r\n")
                self._chan.write(self._prompt)
                return
            
            # Log the received command for debugging purposes
            ecs_log("info", f"SSH command received from {self.clientID}: {user_request}")
            
            # Handle the command asynchronously to avoid blocking the event loop
            asyncio.create_task(self.handle_command(user_request))

    async def handle_command(self, user_request: str):
        ecs_log("info",f"Handling SSH command: {user_request}")

        # Close connection if the user enters "exit"
        if user_request.lower() == "exit":
            ecs_log("info", f"SSH session closed by user {self.clientID}.")
            self._chan.write("Goodbye!\r\n")
            self._chan.close()
            return

        system_prompt = f"""{userprompt} \n. Your response should just contain the command output and be formatted like this ssh-response#####your-response\n"""

        try:
            # Generate a response including the complete history as context
            ai_response=await self.aiclient.generate_response(prompt=f"""Current received command: {user_request}\nLast received commands and given responses: {client_session_history[self.clientID]}""", system_instructions=system_prompt)
            formater, response = ai_response.split("#####")
        except Exception as e:
            ecs_log("error", f"Failed to generate AI response. Error: {str(e)}")
            
        ecs_log("info", f"AI response generated for {self.clientID}: {response}")
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
        ecs_log("info","SSH server initialized.")
    

    def password_auth_supported(self):
        return True

    def validate_password(self, username, password):
        ecs_log("info", f"SSH login attempt with username: {username} and password: {password}")
        if password == self.config["ssh"]["acceptedPassword"]:
            ecs_log("info", f"SSH login successful for username: {username}.")
            return True
        else:
            ecs_log("info", f"SSH login failed for username: {username} with incorrect password {password}.")
            return False

    def session_requested(self):
        ecs_log("info",f"SSH session requested.")
        return SSHServerSession(self.config, self.aiclient)
    
    def connection_lost(self, exc: Optional[Exception]) -> None:
        if exc:
            ecs_log("error", f"SSH connection error: {exc}")
        else:
            ecs_log("info", "SSH connection closed gracefully.")

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
        ecs_log("info","No ssh host key file provided. Generating new one for SSH service.")
        key = asyncssh.generate_private_key("ssh-rsa")
        with open(host_key_file, "wb") as f:
            f.write(key.export_private_key())
        os.chmod(host_key_file, 0o600)
        ecs_log("info","New ssh host key file generated.")

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

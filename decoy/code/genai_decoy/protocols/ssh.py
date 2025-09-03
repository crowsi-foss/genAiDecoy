import asyncio
import asyncssh
import os
import uuid
import json
from genai_decoy.logging import ecs_log
from collections import deque
from typing import Optional

# SessionManager to encapsulate session history
class SessionManager:
    def __init__(self, maxlen=10):
        self._sessions = {}
        self._maxlen = maxlen

    def create_session(self, session_id):
        self._sessions[session_id] = deque(maxlen=self._maxlen)

    def get_history(self, session_id):
        return self._sessions.get(session_id, deque(maxlen=self._maxlen))

    def append_history(self, session_id, command, response):
        if session_id not in self._sessions:
            self.create_session(session_id)
        self._sessions[session_id].append({"command": command, "response": response})

    def remove_session(self, session_id):
        if session_id in self._sessions:
            del self._sessions[session_id]


session_manager = None  # Will be initialized in start_ssh_service
userprompt = ""



class SSHServerSession(asyncssh.SSHServerSession):
    def __init__(self, config, aiclient, session_id, username=None):
        self._input_buffer = ""
        self._prompt = config["ssh"]["sshLinePrefix"]
        self.config = config
        self.aiclient = aiclient
        self.session_id = session_id
        self.username = username
        self._chan = None

    def connection_made(self, chan):
        global session_manager
        self._chan = chan
        # Log session start with session_id and username
        ecs_log("info", f"SSH session established. Session ID: {self.session_id}, Username: {self.username}")
        # Initialize history for this session
        session_manager.create_session(self.session_id)
        self._chan.write(f"""{self.config["ssh"]["banner"]}\r\n""")
        self._chan.write(self._prompt)

    def shell_requested(self):
        ecs_log("info", f"SSH shell requested. Session ID: {self.session_id}, Username: {self.username}")
        return True  # Accept interactive shell

    def data_received(self, data, datatype):
        ecs_log("info", f"SSH data received. Session ID: {self.session_id}, Username: {self.username}, Data: {data}")
        self._input_buffer += data
        if "\n" in self._input_buffer or "\r" in self._input_buffer:
            user_request = self._input_buffer.strip()
            self._input_buffer = ""
            if not user_request:
                self._chan.write("\r\n")
                self._chan.write(self._prompt)
                return
            ecs_log("info", f"SSH command received. Session ID: {self.session_id}, Username: {self.username}, Command: {user_request}")
            asyncio.create_task(self.handle_command(user_request))

    async def handle_command(self, user_request: str):
        global session_manager
        ecs_log("info", f"Handling SSH command. Session ID: {self.session_id}, Username: {self.username}, Command: {user_request}")
        if user_request.lower() == "exit":
            ecs_log("info", f"SSH session closed by user. Session ID: {self.session_id}, Username: {self.username}")
            self._chan.write("Goodbye!\r\n")
            self._chan.close()
            # Remove session history on exit
            session_manager.remove_session(self.session_id)
            return

        system_prompt = f"""{userprompt} \n. Your response must be a JSON object with a single key "response" that contains the command output as a string. For example: {{"response": "your-response-here"}}"""
        try:
            history = list(session_manager.get_history(self.session_id))
            ai_response = await self.aiclient.generate_response(
                prompt=f"Current received command: {user_request}\nLast received commands and given responses: {history}",
                system_instructions=system_prompt
            )

            try:
                # Find the start and end of the JSON block
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1

                if json_start != -1 and json_end != 0:
                    json_str = ai_response[json_start:json_end]
                    # Attempt to parse the extracted JSON response
                    response_data = json.loads(json_str)
                    response = response_data["response"]
                else:
                    # If no JSON block is found, fallback to the raw response
                    ecs_log("warning", f"No JSON object found in AI response. Session ID: {self.session_id}, Username: {self.username}, Raw Response: {ai_response}")
                    response = ai_response

            except (json.JSONDecodeError, KeyError) as e:
                ecs_log("error", f"Failed to parse AI JSON response. Session ID: {self.session_id}, Username: {self.username}, Error: {str(e)}, Raw Response: {ai_response}")
                # Fallback to using the raw response if parsing fails
                response = ai_response

        except Exception as e:
            ecs_log("error", f"Failed to generate AI response. Session ID: {self.session_id}, Username: {self.username}, Error: {str(e)}")
            response = "[AI response error]"

        ecs_log("info", f"AI response generated. Session ID: {self.session_id}, Username: {self.username}, Response: {response}")
        self._chan.write(response + "\r\n")
        self._chan.write(self._prompt)
        session_manager.append_history(self.session_id, user_request, response)

    def eof_received(self):
        return True

    def connection_lost(self, exc):
        global session_manager
        ecs_log("info", f"SSH session terminated. Session ID: {self.session_id}, Username: {self.username}")
        session_manager.remove_session(self.session_id)



class SSHServer(asyncssh.SSHServer):
    def __init__(self, config, aiclient):
        self.config = config
        self.aiclient = aiclient
        self._last_username = None
        ecs_log("info", "SSH server initialized.")

    def password_auth_supported(self):
        return True

    def validate_password(self, username, password):
        ecs_log("info", f"SSH login attempt. Username: {username}, Password: {password}")
        self._last_username = username
        if password == self.config["ssh"]["acceptedPassword"]:
            ecs_log("info", f"SSH login successful. Username: {username}")
            return True
        else:
            ecs_log("info", f"SSH login failed. Username: {username}, Incorrect password: {password}")
            return False

    def session_requested(self):
        ecs_log("info", "SSH session requested.")
        # Generate a unique session ID for every session
        session_id = str(uuid.uuid4())
        username = self._last_username
        return SSHServerSession(self.config, self.aiclient, session_id, username)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        if exc:
            ecs_log("error", f"SSH connection error: {exc}")
        else:
            ecs_log("info", "SSH connection closed gracefully.")

async def start_ssh_service(config, aiclient):
    # Update session maxlen from config
    maxlen = config.get("userInputBuffering", 10)
    global session_manager
    session_manager = SessionManager(maxlen=maxlen)

    global userprompt
    userprompt = f"""{config["baseprompt"]}\n{config["ssh"]["sshprompt"]}"""

    # Path to the SSH host key file
    host_key_file = config["ssh"]["host_key_path"]
    if not os.path.exists(host_key_file):
        ecs_log("info", "No ssh host key file provided. Generating new one for SSH service.")
        key = asyncssh.generate_private_key("ssh-rsa")
        with open(host_key_file, "wb") as f:
            f.write(key.export_private_key())
        os.chmod(host_key_file, 0o600)
        ecs_log("info", "New ssh host key file generated.")

    try:
        server = await asyncssh.create_server(
            lambda: SSHServer(config, aiclient),
            "0.0.0.0",
            config["port"],
            server_host_keys=[host_key_file],
            sftp_factory=None,
        )
        ecs_log("info", "SSH service started")
        await server.wait_closed()
    except Exception as exc:
        ecs_log("error", f"Failed to start SSH service: {exc}")

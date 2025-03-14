import yaml
import os
from genai_decoy.logging import ecs_log

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "config.yaml")

def load_config():
    """Loads configuration from a JSON file."""
    try:
        with open(CONFIG_PATH, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        ecs_log("error", "Failed to load configuration", error=str(e))
        raise SystemExit("Configuration loading failed. Exiting...")

def validate_config(config):
    """Validates required fields in the configuration."""
    required_fields = ["protocol", "port", "genai_provider", "prompt", "api_key_env_var"]
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required config field: {field}")

    if config["protocol"] not in ["http"]:
        raise ValueError("Invalid protocol specified. Only 'http' is supported.")

    if config["genai_provider"] not in ["openai", "gemini"]:
        raise ValueError("Unsupported GenAI provider specified.")

    if not isinstance(config["port"], int) or not (1 <= config["port"] <= 65535):
        raise ValueError("Port must be an integer between 1 and 65535.")

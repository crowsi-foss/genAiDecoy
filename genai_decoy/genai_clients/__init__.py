import os

from genai_decoy.logging import ecs_log
from .geminiclient import GeminiClient

def get_genai_client(config):
    """Returns an appropriate GenAI client based on the specified provider."""
    api_key = os.getenv(config["api_key_env_var"])
    if not api_key:
        raise SystemExit("API key is required but missing. Exiting...")

    if config["genai_provider"] == "gemini":
        return GeminiClient(api_key, config)
    else:
        ecs_log("error", "GenAI provider not supported", provider=config["genai_provider"])
        raise ValueError("Unsupported GenAI provider")

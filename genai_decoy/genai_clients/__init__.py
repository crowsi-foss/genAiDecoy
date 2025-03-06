import os
from .openaiclient import OpenAIClient
from .geminiclient import GeminiClient

def get_genai_client(config):
    """Returns an appropriate GenAI client based on the specified provider."""
    api_key = os.getenv(config["api_key_env_var"])
    if not api_key:
        raise SystemExit("API key is required but missing. Exiting...")

    if config["genai_provider"] == "openai":
        return OpenAIClient(api_key, config)
    elif config["genai_provider"] == "gemini":
        return GeminiClient(api_key, config)
    else:
        raise ValueError("Unsupported GenAI provider")

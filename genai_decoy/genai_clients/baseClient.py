from abc import ABC, abstractmethod

from genai_decoy.logging import ecs_log

class GenAIClient(ABC):
    """Abstract base class for GenAI clients."""
    def __init__(self, api_key, config):
        self.api_key = api_key
        self.config = config

    @abstractmethod
    async def generate_response(self, input_text):
        pass
        raise NotImplementedError("Subclasses should implement this method")

    async def close(self):
        """Closes the session to free up resources."""
        ecs_log("genai_client", "Closing GenAI client")
        await self.session.close()

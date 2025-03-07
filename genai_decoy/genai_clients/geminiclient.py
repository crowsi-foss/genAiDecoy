from .baseClient import GenAIClient
from genai_decoy.logging import ecs_log
from google import genai

class GeminiClient(GenAIClient):
    def __init__(self, api_key, config):
        super().__init__(api_key, config)
        self.client = genai.Client(api_key=api_key)
        self.model=config["model"]

    async def generate_response(self, input_text):
        """Sends a prompt to the Gemini API and returns the generated response."""
        try:
            response = await self.client.aio.models.generate_content(model=self.model, contents=input_text)
            if response.status_code != 200:
                ecs_log("error", "Gemini API request failed", status=response.status_code)
                return "Error: Failed to fetch response."
            return response.json().get("candidates", [{}])[0].get("output", "")
        except Exception as e:
            ecs_log("error", "Unexpected error during Gemini generation", error=str(e))
            return "Error: Unexpected issue occurred."

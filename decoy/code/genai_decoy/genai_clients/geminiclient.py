import json
import re
from .baseClient import GenAIClient
from genai_decoy.logging import ecs_log
from google import genai
from google.genai import types

class GeminiClient(GenAIClient):
    def __init__(self, api_key, config):
        super().__init__(api_key, config)
        self.client = genai.Client(api_key=api_key)
        self.model=config["model"]
        self.temperature=config["temperature"]
        self.max_output_tokens=config["max_output_tokens"]

    async def generate_response(self, prompt, system_instructions):
        """Sends a prompt to the Gemini API and returns the generated response."""
        try:
            ai_response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt, 
                config=types.GenerateContentConfig(
                    system_instruction=system_instructions,
                    max_output_tokens=self.max_output_tokens,
                    temperature=self.temperature,
                ),
            )
            return ai_response.text
        except Exception as e:
            ecs_log("error", "Unexpected error during Gemini generation", error=str(e))
            return "Error: Unexpected issue occurred."

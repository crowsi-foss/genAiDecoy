from .baseClient import GenAIClient
from genai_decoy.logging import ecs_log

class GeminiClient(GenAIClient):
    async def generate_response(self, input_text):
        """Sends a prompt to the Gemini API and returns the generated response."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {"prompt": input_text}
            url = f"https://generativelanguage.googleapis.com/v1/models/text-bison:generate?key={self.api_key}"
            async with self.session.post(url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    ecs_log("error", "Gemini API request failed", status=resp.status)
                    return "Error: Failed to fetch response."
                data = await resp.json()
                return data.get("candidates", [{}])[0].get("output", "")
        except Exception as e:
            ecs_log("error", "Unexpected error during Gemini generation", error=str(e))
            return "Error: Unexpected issue occurred."

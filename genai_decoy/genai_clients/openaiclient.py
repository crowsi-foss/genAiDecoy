from .baseClient import GenAIClient
from genai_decoy.logging import ecs_log

class OpenAIClient(GenAIClient):
    async def generate_response(self, input_text):
        """Sends a prompt to the OpenAI API and returns the generated response."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {
                "model": self.config.get("model", "gpt-4"),
                "messages": [{"role": "user", "content": input_text}]
            }
            async with self.session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload) as resp:
                if resp.status != 200:
                    ecs_log("error", "OpenAI API request failed", status=resp.status)
                    return "Error: Failed to fetch response."
                data = await resp.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            ecs_log("error", "Unexpected error during OpenAI generation", error=str(e))
            return "Error: Unexpected issue occurred."

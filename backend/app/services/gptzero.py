from fastapi import HTTPException
import httpx
import os

class GPTZeroService:
    def __init__(self):
        self.api_key = os.getenv("GPTZERO_API_KEY")
        self.api_url = "https://api.gptzero.me/v2/predict/text"

    async def analyze(self, text: str):
        if not self.api_key or self.api_key == "your_key_here":
            return {
                "ai_probability": 0.0,
                "message": "GPTZero API key not configured"
            }

        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {"document": text}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.api_url, headers=headers, json=payload)
                
                if response.status_code != 200:
                    return {
                        "ai_probability": 0.0,
                        "error": f"API error: {response.status_code}"
                    }
                
                data = response.json()
                return {
                    "ai_probability": data.get("documents", [{}])[0].get("completely_generated_prob", 0.0),
                    "class_probabilities": data.get("documents", [{}])[0].get("class_probabilities", {})
                }
        except Exception as e:
            return {
                "ai_probability": 0.0,
                "error": str(e)
            }

# Export wrapper function for router
async def detect_text(text: str):
    service = GPTZeroService()
    return await service.analyze(text)
from fastapi import HTTPException
import requests
import os
import asyncio

class GPTZeroService:
    def __init__(self):
        self.api_key = os.getenv("GPTZERO_API_KEY")
        self.api_url = "https://api.gptzero.me/detect"

    async def detect_text(self, text: str):
        if not self.api_key:
            raise HTTPException(status_code=500, detail="GPTZero API key not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {"text": text}

        response = requests.post(self.api_url, headers=headers, json=payload)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("error", "Unknown error"))

        return response.json()

# Export wrapper function for router
_service = GPTZeroService()

async def detect_text(text: str):
    return await _service.detect_text(text)
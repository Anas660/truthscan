"""GPTZero service helper."""
import os
import httpx

GPTZERO_API_KEY = os.getenv("GPTZERO_API_KEY", "")
GPTZERO_URL = "https://api.gptzero.me/v2/predict/text"


async def predict_text(text: str) -> dict:
    """Call GPTZero and return raw response dict."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            GPTZERO_URL,
            headers={"x-api-key": GPTZERO_API_KEY, "Content-Type": "application/json"},
            json={"document": text, "multilingual": False},
        )
        resp.raise_for_status()
        return resp.json()

from fastapi import HTTPException
import requests
import os

class ElevenLabsService:
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.audio_detection_url = os.getenv("ELEVENLABS_AUDIO_DETECTION_URL")

    def detect_audio(self, audio_file):
        if not self.api_key or not self.audio_detection_url:
            raise HTTPException(status_code=500, detail="API key or URL not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        files = {'file': audio_file}
        response = requests.post(self.audio_detection_url, headers=headers, files=files)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error during audio detection"))

        return response.json()
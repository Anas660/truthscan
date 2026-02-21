from fastapi import HTTPException
import requests
import os

class ElevenLabsService:
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.audio_detection_url = os.getenv("ELEVENLABS_AUDIO_DETECTION_URL", "https://api.elevenlabs.io/v1/audio-detection")

    def detect_audio(self, audio_file):
        if not self.api_key:
            raise HTTPException(status_code=500, detail="ElevenLabs API key not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        files = {'file': audio_file}
        response = requests.post(self.audio_detection_url, headers=headers, files=files)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Error during audio detection"))

        return response.json()

# Export wrapper function for router
_service = ElevenLabsService()

def detect_audio(audio_data: bytes):
    return _service.detect_audio(audio_data)
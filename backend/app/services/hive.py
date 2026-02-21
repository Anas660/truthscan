# Hive Moderation Service

import requests
import os
from fastapi import UploadFile
import tempfile

class HiveModeration:
    def __init__(self):
        self.api_key = os.getenv("HIVE_API_KEY")
        self.api_url = "https://api.thehive.ai/v1/moderation"

    def detect_image(self, image_path):
        with open(image_path, 'rb') as image_file:
            files = {'file': image_file}
            headers = {'Authorization': f'Bearer {self.api_key}'}
            response = requests.post(self.api_url, headers=headers, files=files)
            return response.json() if response.status_code == 200 else None

    def check_image(self, image_path):
        result = self.detect_image(image_path)
        if result:
            return {
                "verdict": result.get("verdict"),
                "confidence": result.get("confidence"),
                "details": result.get("details")
            }
        return {"error": "Failed to process the image."}

# Export wrapper function for router
_service = HiveModeration()

async def detect_image(file: UploadFile):
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name
    
    try:
        result = _service.check_image(temp_path)
        return result
    finally:
        import os as os_module
        if os_module.path.exists(temp_path):
            os_module.remove(temp_path)
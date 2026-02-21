# Hive Moderation Service

import requests
import os

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
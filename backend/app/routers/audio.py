from fastapi import APIRouter, File, UploadFile
from services.elevenlabs import detect_audio

router = APIRouter()

@router.post("/detect/audio")
async def detect_audio_endpoint(file: UploadFile = File(...)):
    """
    Endpoint to detect AI-generated audio.
    """
    audio_data = await file.read()
    result = detect_audio(audio_data)
    return result
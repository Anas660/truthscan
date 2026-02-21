from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict
from app.services.video_analyzer import analyze_video

router = APIRouter()

@router.post("/detect/video")
async def detect_video(file: UploadFile = File(...)) -> Dict[str, str]:
    if not file.filename.endswith(('.mp4', '.mov', '.webm')):
        raise HTTPException(status_code=400, detail="Invalid file format. Only MP4, MOV, and WEBM are supported.")
    
    try:
        result = await analyze_video(file)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

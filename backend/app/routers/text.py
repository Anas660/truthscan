from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.gptzero import detect_text
from services.hive import detect_image

router = APIRouter()

class TextRequest(BaseModel):
    text: str

@router.post("/detect/text")
async def detect_ai_text(request: TextRequest):
    try:
        result = await detect_text(request.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
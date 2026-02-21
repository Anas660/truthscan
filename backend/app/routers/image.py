from fastapi import APIRouter, File, UploadFile
from services.hive import detect_image
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/detect/image")
async def detect_image_endpoint(file: UploadFile = File(...)):
    try:
        result = await detect_image(file)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
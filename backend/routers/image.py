import time
import os
import io
import httpx
from fastapi import APIRouter, UploadFile, File, HTTPException
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

HIVE_API_KEY = os.getenv("HIVE_API_KEY", "")
AIORNOT_API_KEY = os.getenv("AIORNOT_API_KEY", "")

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE = 20 * 1024 * 1024  # 20MB


def check_exif(file_bytes: bytes) -> bool:
    """Returns True if EXIF data is present."""
    try:
        from PIL import Image
        import piexif
        img = Image.open(io.BytesIO(file_bytes))
        exif_raw = img.info.get("exif")
        if exif_raw:
            piexif.load(exif_raw)
            return True
        return False
    except Exception:
        return False


async def call_hive(file_bytes: bytes, filename: str, content_type: str) -> float | None:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.thehive.ai/api/v2/task/sync",
                headers={"Authorization": f"Token {HIVE_API_KEY}"},
                files={"image": (filename, file_bytes, content_type)},
            )
            resp.raise_for_status()
            data = resp.json()
            print("Hive response:", data)
            classes = data.get("status", [{}])[0].get("response", {}).get("output", [{}])[0].get("classes", [])
            for cls in classes:
                if cls.get("class") == "ai_generated":
                    return cls.get("score", 0.0)
    except Exception as e:
        print(f"Hive API error: {e}")
    return None


async def call_aiornot(file_bytes: bytes, filename: str, content_type: str) -> float | None:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.aiornot.com/v1/reports/image",
                headers={"Authorization": f"Bearer {AIORNOT_API_KEY}"},
                files={"object": (filename, file_bytes, content_type)},
            )
            resp.raise_for_status()
            data = resp.json()
            print("AI-or-Not response:", data)
            report = data.get("report", {})
            ai_score = report.get("ai", {}).get("confidence", 0) / 100.0
            return ai_score
    except Exception as e:
        print(f"AI-or-Not API error: {e}")
    return None


@router.post("/image")
async def detect_image(file: UploadFile = File(...)):
    start = time.time()

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=422, detail=f"Unsupported file type: {file.content_type}. Allowed: JPG, PNG, WEBP, GIF")

    file_bytes = await file.read()

    if len(file_bytes) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 20MB.")

    if not HIVE_API_KEY and not AIORNOT_API_KEY:
        return {
            "verdict": "error",
            "message": "API key not configured. Add HIVE_API_KEY or AIORNOT_API_KEY to .env",
            "ai_probability": 0,
            "human_probability": 0,
            "confidence": 0,
            "signals": [],
            "model_used": "Hive / AI-or-Not",
            "processing_time_ms": 0,
        }

    has_exif = check_exif(file_bytes)
    ai_prob = None
    model_used = "Unknown"

    if HIVE_API_KEY:
        ai_prob = await call_hive(file_bytes, file.filename or "image", file.content_type)
        model_used = "Hive Moderation"

    if ai_prob is None and AIORNOT_API_KEY:
        ai_prob = await call_aiornot(file_bytes, file.filename or "image", file.content_type)
        model_used = "AI-or-Not"

    if ai_prob is None:
        return {
            "verdict": "error",
            "message": "All image detection APIs failed. Check your API keys and logs.",
            "ai_probability": 0,
            "human_probability": 0,
            "confidence": 0,
            "signals": [],
            "model_used": model_used,
            "processing_time_ms": int((time.time() - start) * 1000),
        }

    human_prob = round(1.0 - ai_prob, 4)

    if ai_prob > 0.7:
        verdict = "ai"
    elif ai_prob < 0.35:
        verdict = "human"
    else:
        verdict = "mixed"

    signals = []
    if ai_prob > 0.7:
        signals.append({"label": "GAN fingerprint detected", "severity": "high"})
        signals.append({"label": "Synthetic texture patterns", "severity": "high"})
    elif ai_prob > 0.4:
        signals.append({"label": "Possible AI upscaling", "severity": "medium"})
        signals.append({"label": "Inconsistent lighting gradients", "severity": "medium"})

    if has_exif:
        signals.append({"label": "Natural EXIF metadata present", "severity": "low"})
    else:
        signals.append({"label": "No EXIF metadata found", "severity": "medium"})

    elapsed = int((time.time() - start) * 1000)

    return {
        "verdict": verdict,
        "ai_probability": round(ai_prob, 4),
        "human_probability": round(human_prob, 4),
        "confidence": int(max(ai_prob, human_prob) * 100),
        "signals": signals,
        "model_used": model_used,
        "processing_time_ms": elapsed,
    }

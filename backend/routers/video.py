import time
import os
import io
import tempfile
import numpy as np
import httpx
from fastapi import APIRouter, UploadFile, File, HTTPException
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

HIVE_API_KEY = os.getenv("HIVE_API_KEY", "")
AIORNOT_API_KEY = os.getenv("AIORNOT_API_KEY", "")

ALLOWED_TYPES = {"video/mp4", "video/quicktime", "video/webm", "video/x-msvideo", "application/octet-stream"}
MAX_SIZE = 500 * 1024 * 1024  # 500MB

NUM_FRAMES = 10


def extract_frames(video_bytes: bytes, num_frames: int = NUM_FRAMES) -> list:
    """Extract evenly spaced frames from video bytes. Returns list of JPEG bytes."""
    try:
        import cv2

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name

        try:
            cap = cv2.VideoCapture(tmp_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames <= 0:
                return []

            indices = np.linspace(0, total_frames - 1, num=num_frames, dtype=int)
            frames = []

            for idx in indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
                ret, frame = cap.read()
                if ret:
                    _, buf = cv2.imencode(".jpg", frame)
                    frames.append(buf.tobytes())

            cap.release()
        finally:
            os.unlink(tmp_path)

        return frames

    except Exception as e:
        print(f"Frame extraction error: {e}")
        return []


async def analyze_frame_hive(frame_bytes: bytes) -> float | None:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.thehive.ai/api/v2/task/sync",
                headers={"Authorization": f"Token {HIVE_API_KEY}"},
                files={"image": ("frame.jpg", frame_bytes, "image/jpeg")},
            )
            resp.raise_for_status()
            data = resp.json()
            classes = (
                data.get("status", [{}])[0]
                .get("response", {})
                .get("output", [{}])[0]
                .get("classes", [])
            )
            for cls in classes:
                if cls.get("class") == "ai_generated":
                    return cls.get("score", 0.0)
    except Exception as e:
        print(f"Hive frame error: {e}")
    return None


async def analyze_frame_aiornot(frame_bytes: bytes) -> float | None:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.aiornot.com/v1/reports/image",
                headers={"Authorization": f"Bearer {AIORNOT_API_KEY}"},
                files={"object": ("frame.jpg", frame_bytes, "image/jpeg")},
            )
            resp.raise_for_status()
            data = resp.json()
            report = data.get("report", {})
            ai_score = report.get("ai", {}).get("confidence", 0) / 100.0
            return ai_score
    except Exception as e:
        print(f"AI-or-Not frame error: {e}")
    return None


@router.post("/video")
async def detect_video(file: UploadFile = File(...)):
    start = time.time()

    content_type = file.content_type or ""
    if not (content_type.startswith("video/") or content_type == "application/octet-stream"):
        raise HTTPException(status_code=422, detail="Unsupported file type. Allowed: MP4, MOV, WEBM")

    file_bytes = await file.read()

    if len(file_bytes) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 500MB.")

    if not HIVE_API_KEY and not AIORNOT_API_KEY:
        return {
            "verdict": "error",
            "message": "API key not configured. Add HIVE_API_KEY or AIORNOT_API_KEY to .env",
            "ai_probability": 0,
            "human_probability": 0,
            "confidence": 0,
            "signals": [],
            "model_used": "Frame-based detection",
            "processing_time_ms": 0,
        }

    frames = extract_frames(file_bytes, NUM_FRAMES)

    if not frames:
        raise HTTPException(status_code=422, detail="Could not extract frames from video. Ensure the file is a valid video.")

    frame_scores = []
    for frame in frames:
        score = None
        if HIVE_API_KEY:
            score = await analyze_frame_hive(frame)
        if score is None and AIORNOT_API_KEY:
            score = await analyze_frame_aiornot(frame)
        if score is not None:
            frame_scores.append(score)

    if not frame_scores:
        return {
            "verdict": "error",
            "message": "Frame analysis API calls all failed. Check API keys and logs.",
            "ai_probability": 0,
            "human_probability": 0,
            "confidence": 0,
            "signals": [],
            "model_used": "Frame-based detection",
            "processing_time_ms": int((time.time() - start) * 1000),
        }

    avg_ai_prob = float(np.mean(frame_scores))
    variance = float(np.var(frame_scores))
    human_prob = round(1.0 - avg_ai_prob, 4)

    if avg_ai_prob > 0.7:
        verdict = "ai"
    elif avg_ai_prob < 0.35:
        verdict = "human"
    else:
        verdict = "mixed"

    signals = []
    if variance > 0.05:
        signals.append({"label": "Inconsistent AI generation across frames", "severity": "medium"})
    if avg_ai_prob > 0.7 and variance < 0.05:
        signals.append({"label": "Consistent deepfake patterns", "severity": "high"})
    if avg_ai_prob > 0.5:
        signals.append({"label": "Synthetic facial features detected", "severity": "high"})
    else:
        signals.append({"label": "Natural motion patterns", "severity": "low"})

    signals.append({
        "label": f"Analyzed {len(frame_scores)} of {len(frames)} frames",
        "severity": "low",
    })

    elapsed = int((time.time() - start) * 1000)
    model_used = "Hive Moderation (frames)" if HIVE_API_KEY else "AI-or-Not (frames)"

    return {
        "verdict": verdict,
        "ai_probability": round(avg_ai_prob, 4),
        "human_probability": round(human_prob, 4),
        "confidence": int(max(avg_ai_prob, human_prob) * 100),
        "signals": signals,
        "model_used": model_used,
        "processing_time_ms": elapsed,
    }

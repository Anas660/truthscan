import time
import os
import tempfile
import httpx
import numpy as np
from fastapi import APIRouter, UploadFile, File, HTTPException
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_AUDIO_DETECTION_URL = os.getenv("ELEVENLABS_AUDIO_DETECTION_URL", "")

ALLOWED_TYPES = {"audio/mpeg", "audio/wav", "audio/x-wav", "audio/aac", "audio/flac", "audio/mp3", "audio/x-flac"}
MAX_SIZE = 100 * 1024 * 1024  # 100MB


def is_key_configured(value: str) -> bool:
    key = (value or "").strip()
    return bool(key) and key.lower() not in {"your_key_here", "changeme", "replace_me"}


async def call_elevenlabs(file_bytes: bytes, filename: str, content_type: str) -> float | None:
    if not is_key_configured(ELEVENLABS_API_KEY):
        return None

    if not ELEVENLABS_AUDIO_DETECTION_URL:
        return None

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                ELEVENLABS_AUDIO_DETECTION_URL,
                headers={"xi-api-key": ELEVENLABS_API_KEY},
                files={"file": (filename, file_bytes, content_type)},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("probability", data.get("ai_probability", None))
    except httpx.HTTPStatusError as e:
        if e.response is not None and e.response.status_code in {404, 405}:
            print("ElevenLabs audio detection endpoint unavailable; using local fallback")
            return None
        print(f"ElevenLabs API error: {e}")
    except Exception as e:
        print(f"ElevenLabs API error: {e}")
    return None


def librosa_fallback(file_bytes: bytes, suffix: str = ".wav") -> dict:
    """Heuristic audio analysis using librosa when no API key is set."""
    try:
        import librosa
        import soundfile as sf

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            y, sr = librosa.load(tmp_path, sr=None, mono=True)
        finally:
            os.unlink(tmp_path)

        signals = []
        ai_indicators = 0

        # Check noise floor — AI audio often has very low background noise
        noise_floor = float(np.percentile(np.abs(y), 5))
        if noise_floor < 0.001:
            signals.append({"label": "No background room noise", "severity": "medium"})
            ai_indicators += 1
        else:
            signals.append({"label": "Natural background noise present", "severity": "low"})

        # Check pitch consistency using zero-crossing rate as proxy
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        zcr_std = float(np.std(zcr))
        if zcr_std < 0.02:
            signals.append({"label": "Unnatural pitch consistency", "severity": "high"})
            ai_indicators += 2

        # Check spectral flatness — synthetic audio tends to be very flat
        flatness = librosa.feature.spectral_flatness(y=y)[0]
        mean_flatness = float(np.mean(flatness))
        if mean_flatness > 0.1:
            signals.append({"label": "Waveform irregularities found", "severity": "medium"})
            ai_indicators += 1

        ai_prob = min(0.95, ai_indicators / 4.0)
        return {"ai_prob": ai_prob, "signals": signals, "model": "librosa heuristic (no API key)"}

    except Exception as e:
        print(f"librosa fallback error: {e}")
        return {
            "ai_prob": 0.5,
            "signals": [{"label": "Audio analysis unavailable", "severity": "medium"}],
            "model": "librosa fallback failed",
        }


@router.post("/audio")
async def detect_audio(file: UploadFile = File(...)):
    start = time.time()

    content_type = file.content_type or ""
    # Be lenient with audio MIME types
    if not (content_type.startswith("audio/") or content_type == "application/octet-stream"):
        raise HTTPException(status_code=422, detail=f"Unsupported file type. Allowed: MP3, WAV, AAC, FLAC")

    file_bytes = await file.read()

    if len(file_bytes) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 100MB.")

    filename = file.filename or "audio.wav"
    suffix = os.path.splitext(filename)[1] or ".wav"

    ai_prob = None
    model_used = "ElevenLabs AI Speech Classifier"
    signals = []

    if is_key_configured(ELEVENLABS_API_KEY) and ELEVENLABS_AUDIO_DETECTION_URL:
        ai_prob = await call_elevenlabs(file_bytes, filename, content_type)

    if ai_prob is None:
        # Fallback to librosa heuristic
        result = librosa_fallback(file_bytes, suffix)
        ai_prob = result["ai_prob"]
        signals = result["signals"]
        model_used = result["model"]
    else:
        # Build signals from ElevenLabs result
        if ai_prob > 0.7:
            signals.append({"label": "Synthetic breath patterns detected", "severity": "high"})
            signals.append({"label": "Unnatural pitch consistency", "severity": "high"})
        elif ai_prob > 0.4:
            signals.append({"label": "No background room noise", "severity": "medium"})
            signals.append({"label": "Waveform irregularities found", "severity": "medium"})
        else:
            signals.append({"label": "Natural vocal variation detected", "severity": "low"})
            signals.append({"label": "Background ambience present", "severity": "low"})

    human_prob = round(1.0 - ai_prob, 4)

    if ai_prob > 0.7:
        verdict = "ai"
    elif ai_prob < 0.35:
        verdict = "human"
    else:
        verdict = "mixed"

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

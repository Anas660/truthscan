"""ElevenLabs AI Speech Classifier service helper."""
import os
import httpx

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_URL = os.getenv("ELEVENLABS_AUDIO_DETECTION_URL", "")


def is_key_configured(value: str) -> bool:
    key = (value or "").strip()
    return bool(key) and key.lower() not in {"your_key_here", "changeme", "replace_me"}


async def detect_audio(file_bytes: bytes, filename: str, content_type: str) -> float | None:
    """Returns AI probability from ElevenLabs, or None on failure."""
    if not is_key_configured(ELEVENLABS_API_KEY) or not ELEVENLABS_URL:
        return None

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                ELEVENLABS_URL,
                headers={"xi-api-key": ELEVENLABS_API_KEY},
                files={"file": (filename, file_bytes, content_type)},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("probability", data.get("ai_probability", None))
    except httpx.HTTPStatusError as e:
        if e.response is not None and e.response.status_code in {404, 405}:
            print("ElevenLabs audio detection endpoint unavailable; using fallback")
            return None
        print(f"ElevenLabs error: {e}")
    except Exception as e:
        print(f"ElevenLabs error: {e}")
    return None

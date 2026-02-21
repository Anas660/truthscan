"""Hive Moderation and AI-or-Not service helpers."""
import os
import httpx

HIVE_API_KEY = os.getenv("HIVE_API_KEY", "")
AIORNOT_API_KEY = os.getenv("AIORNOT_API_KEY", "")


async def hive_detect_image(file_bytes: bytes, filename: str, content_type: str) -> float | None:
    """Returns AI probability score from Hive Moderation, or None on failure."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.thehive.ai/api/v2/task/sync",
                headers={"Authorization": f"Token {HIVE_API_KEY}"},
                files={"image": (filename, file_bytes, content_type)},
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
        print(f"Hive error: {e}")
    return None


async def aiornot_detect_image(file_bytes: bytes, filename: str, content_type: str) -> float | None:
    """Returns AI probability score from AI-or-Not, or None on failure."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.aiornot.com/v1/reports/image",
                headers={"Authorization": f"Bearer {AIORNOT_API_KEY}"},
                files={"object": (filename, file_bytes, content_type)},
            )
            resp.raise_for_status()
            data = resp.json()
            report = data.get("report", {})
            return report.get("ai", {}).get("confidence", 0) / 100.0
    except Exception as e:
        print(f"AI-or-Not error: {e}")
    return None

import time
import os
import httpx
from fastapi import APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

GPTZERO_API_KEY = os.getenv("GPTZERO_API_KEY", "")
HF_API_KEY = os.getenv("HF_API_KEY", "")
HF_TEXT_MODEL = os.getenv("HF_TEXT_MODEL", "openai-community/roberta-base-openai-detector")


class TextRequest(BaseModel):
    text: str


def build_signals(doc: dict) -> list:
    signals = []
    avg_prob = doc.get("average_generated_prob", 0)
    burstiness = doc.get("burstiness", None)
    perplexity = doc.get("perplexity", None)

    if avg_prob > 0.6:
        signals.append({"label": "High AI probability score", "severity": "high"})
    if burstiness is not None and burstiness < 20:
        signals.append({"label": "Low text burstiness", "severity": "high"})
    if perplexity is not None and perplexity < 30:
        signals.append({"label": "Low perplexity score", "severity": "high"})
    if not signals:
        signals.append({"label": "Natural sentence variety", "severity": "low"})
    return signals


def build_hf_signals(ai_prob: float) -> list:
    if ai_prob > 0.7:
        return [{"label": "Strong classifier AI signal", "severity": "high"}]
    if ai_prob > 0.45:
        return [{"label": "Moderate classifier AI signal", "severity": "medium"}]
    return [{"label": "Classifier leans human-written", "severity": "low"}]


def is_key_configured(value: str) -> bool:
    key = (value or "").strip()
    return bool(key) and key.lower() not in {"your_key_here", "changeme", "replace_me"}


def detect_with_local_heuristic(text: str) -> tuple[float, str, list]:
    normalized = (text or "").strip()
    if not normalized:
        return 0.5, "Local heuristic", [{"label": "Empty text content", "severity": "medium"}]

    words = normalized.split()
    word_count = len(words)
    unique_ratio = len({w.lower().strip('.,!?;:"()[]{}') for w in words if w}) / max(word_count, 1)
    punctuation_count = sum(1 for c in normalized if c in ".,;:!?-")
    punctuation_density = punctuation_count / max(len(normalized), 1)

    score = 0.5
    if word_count > 200:
        score += 0.06
    if unique_ratio < 0.42:
        score += 0.12
    if punctuation_density < 0.015:
        score += 0.08

    ai_prob = max(0.05, min(0.95, score))

    signals = [
        {"label": "Fallback heuristic used (no valid API response)", "severity": "medium"}
    ]
    if unique_ratio < 0.42:
        signals.append({"label": "Low vocabulary variety", "severity": "medium"})
    if punctuation_density < 0.015:
        signals.append({"label": "Low punctuation density", "severity": "medium"})

    return ai_prob, "Local heuristic", signals


async def detect_with_hf(text: str) -> tuple[float, str]:
    if not is_key_configured(HF_API_KEY):
        raise ValueError("HF_API_KEY missing")

    url = f"https://api-inference.huggingface.co/models/{HF_TEXT_MODEL}"
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=45) as client:
        resp = await client.post(url, headers=headers, json={"inputs": text})
        resp.raise_for_status()
        data = resp.json()

    if isinstance(data, list) and data and isinstance(data[0], list):
        candidates = data[0]
    elif isinstance(data, list):
        candidates = data
    else:
        raise ValueError("Unexpected HF response format")

    ai_prob = None
    human_prob = None
    for item in candidates:
        label = str(item.get("label", "")).lower()
        score = float(item.get("score", 0.0))
        if any(token in label for token in ["fake", "ai", "generated", "machine"]):
            ai_prob = score if ai_prob is None else max(ai_prob, score)
        if any(token in label for token in ["real", "human"]):
            human_prob = score if human_prob is None else max(human_prob, score)

    if ai_prob is None and human_prob is None:
        raise ValueError("Could not map HF labels to AI/Human probabilities")

    if ai_prob is None:
        ai_prob = 1.0 - human_prob
    if human_prob is None:
        human_prob = 1.0 - ai_prob

    ai_prob = max(0.0, min(1.0, float(ai_prob)))
    return ai_prob, f"Hugging Face ({HF_TEXT_MODEL})"


async def detect_with_gptzero(text: str) -> tuple[float, dict]:
    if not is_key_configured(GPTZERO_API_KEY):
        raise ValueError("GPTZERO_API_KEY missing")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.gptzero.me/v2/predict/text",
            headers={"x-api-key": GPTZERO_API_KEY, "Content-Type": "application/json"},
            json={"document": text, "multilingual": False},
        )
        resp.raise_for_status()
        data = resp.json()

    doc = data.get("documents", [{}])[0]
    return float(doc.get("completely_generated_prob", 0.0)), doc


@router.post("/text")
async def detect_text(req: TextRequest):
    start = time.time()

    hf_enabled = is_key_configured(HF_API_KEY)
    gptzero_enabled = is_key_configured(GPTZERO_API_KEY)

    try:
        used_provider = None
        doc = None

        if hf_enabled:
            ai_prob, model_used = await detect_with_hf(req.text)
            used_provider = "hf"
        elif gptzero_enabled:
            ai_prob, doc = await detect_with_gptzero(req.text)
            model_used = "GPTZero v2"
            used_provider = "gptzero"
        else:
            ai_prob, model_used, signals = detect_with_local_heuristic(req.text)
            used_provider = "local"
    except Exception as e:
        if gptzero_enabled and hf_enabled:
            try:
                ai_prob, doc = await detect_with_gptzero(req.text)
                model_used = "GPTZero v2"
                used_provider = "gptzero"
            except Exception as fallback_error:
                print(f"Text detector fallback error: {fallback_error}")
                ai_prob, model_used, signals = detect_with_local_heuristic(req.text)
                used_provider = "local"
        else:
            print(f"Text detector error: {e}")
            ai_prob, model_used, signals = detect_with_local_heuristic(req.text)
            used_provider = "local"

    human_prob = round(1.0 - ai_prob, 4)

    if ai_prob > 0.7:
        verdict = "ai"
    elif ai_prob < 0.35:
        verdict = "human"
    else:
        verdict = "mixed"

    if used_provider == "hf":
        signals = build_hf_signals(ai_prob)
    elif used_provider == "gptzero":
        signals = build_signals(doc or {})
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

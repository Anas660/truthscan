# Ai TruthScan

**AI Content Detection Engine** — Ai TruthScan detects whether text, images, video, and audio were AI-generated or human-made, with confidence scores and signal breakdowns.

---

## Features

- **Text** — Hugging Face Inference API (recommended) detects AI-written text, with GPTZero fallback support
- **Image** — Hive Moderation or AI-or-Not API detects AI-generated images + EXIF check
- **Video** — Frame extraction via OpenCV + image detection on sampled frames
- **Audio** — Local librosa heuristic detection by default, with optional external classifier endpoint support
- Animated probability bars, signal chips, loading states, and error toasts

---

## Project Structure

```
truthscan/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   │   ├── text.py
│   │   │   ├── image.py
│   │   │   ├── video.py
│   │   │   └── audio.py
│   │   └── services/
│   │       ├── gptzero.py
│   │       ├── hive.py
│   │       ├── elevenlabs.py
│   │       └── video_analyzer.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── components/
│   │       ├── TabSelector.jsx
│   │       ├── TextPanel.jsx
│   │       ├── ImagePanel.jsx
│   │       ├── VideoPanel.jsx
│   │       └── AudioPanel.jsx
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.js
├── deploy/
│   ├── docker-compose.prod.yml
│   └── nginx.conf
└── README.md
```

---

## Quick Start (Local Development)

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your API keys
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

---

## API Keys

| Service                | Used For                                              | Get Key                                                                  |
| ---------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------ |
| Hugging Face Inference | AI text detection (recommended, lower cost/free tier) | [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) |
| GPTZero                | AI text detection (optional fallback)                 | [gptzero.me/plans](https://gptzero.me/plans)                             |
| Hive Moderation        | AI image detection                                    | [thehive.ai](https://thehive.ai)                                         |
| AI or Not              | AI image detection (backup)                           | [aiornot.com](https://aiornot.com)                                       |
| ElevenLabs             | AI audio/voice detection                              | [elevenlabs.io](https://elevenlabs.io)                                   |

Add your keys to `backend/.env`:

```env
HF_API_KEY=your_key_here
HF_TEXT_MODEL=openai-community/roberta-base-openai-detector
GPTZERO_API_KEY=your_key_here
HIVE_API_KEY=your_key_here
ELEVENLABS_API_KEY=your_key_here
ELEVENLABS_AUDIO_DETECTION_URL=
AIORNOT_API_KEY=your_key_here
```

> **Note:** All detectors fall back gracefully when API keys are missing — the app still runs, just with limited detection capability. Audio falls back to a librosa heuristic analysis.

---

## Docker

```bash
# Copy and fill in API keys first
cp backend/.env.example backend/.env

docker compose -f deploy/docker-compose.prod.yml up --build
# Frontend:  http://localhost:5173
# Backend:  http://localhost:8000
```

---

## API Reference

All detection endpoints return the same shape:

```json
{
  "verdict": "ai" | "human" | "mixed" | "error",
  "ai_probability": 0.91,
  "human_probability": 0.09,
  "confidence": 91,
  "signals": [
    { "label": "Low perplexity score", "severity": "high" },
    { "label": "Natural EXIF metadata present", "severity": "low" }
  ],
  "model_used": "Hugging Face (openai-community/roberta-base-openai-detector)",
  "processing_time_ms": 1240
}
```

| Endpoint        | Method | Body                              |
| --------------- | ------ | --------------------------------- |
| `/detect/text`  | POST   | JSON `{ "text": "..." }`          |
| `/detect/image` | POST   | `multipart/form-data` with `file` |
| `/detect/video` | POST   | `multipart/form-data` with `file` |
| `/detect/audio` | POST   | `multipart/form-data` with `file` |

Signal severity mapping: `high` = red (strong AI indicator) · `medium` = yellow · `low` = green (human indicator)

---

## File Size Limits

| Type  | Formats             | Max Size |
| ----- | ------------------- | -------- |
| Text  | —                   | —        |
| Image | JPG, PNG, WEBP, GIF | 20 MB    |
| Video | MP4, MOV, WEBM      | 500 MB   |
| Audio | MP3, WAV, AAC, FLAC | 100 MB   |
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import text, image, video, audio

app = FastAPI(title="TruthScan API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(text.router, prefix="/detect")
app.include_router(image.router, prefix="/detect")
app.include_router(video.router, prefix="/detect")
app.include_router(audio.router, prefix="/detect")


@app.get("/")
def root():
    return {"message": "TruthScan API is running", "docs": "/docs"}

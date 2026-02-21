from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import text, image, video, audio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(text.router, prefix="/detect", tags=["Text"])
app.include_router(image.router, prefix="/detect", tags=["Image"])
app.include_router(video.router, prefix="/detect", tags=["Video"])
app.include_router(audio.router, prefix="/detect", tags=["Audio"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI TruthScan API"}
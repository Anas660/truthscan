"""Video frame extraction and analysis service."""
import os
import tempfile
import numpy as np


def extract_frames(video_bytes: bytes, num_frames: int = 10) -> list[bytes]:
    """Extract evenly spaced JPEG frames from video bytes."""
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


def compute_temporal_variance(frame_scores: list[float]) -> float:
    """Compute variance of per-frame AI scores to detect temporal inconsistency."""
    if not frame_scores:
        return 0.0
    return float(np.var(frame_scores))

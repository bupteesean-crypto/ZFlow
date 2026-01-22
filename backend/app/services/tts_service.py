from __future__ import annotations

import math
from pathlib import Path
import wave

CHAR_TIME_SEC = 0.12
SAMPLE_RATE = 22050


def estimate_duration(text: str, speed: float) -> float:
    cleaned = text.strip()
    length = len(cleaned)
    if length == 0:
        return 0.0
    safe_speed = max(0.1, float(speed))
    return max(1.0, (length * CHAR_TIME_SEC) / safe_speed)


def synthesize_silent_wav(text: str, speed: float, output_path: Path) -> float:
    duration = estimate_duration(text, speed)
    frames = int(math.ceil(duration * SAMPLE_RATE))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b"\x00\x00" * frames)
    return duration

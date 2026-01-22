from __future__ import annotations

import math
from pathlib import Path
import wave

SAMPLE_RATE = 22050


def synthesize_silent_wav(duration_sec: float, output_path: Path) -> None:
    duration = max(0.5, float(duration_sec))
    frames = int(math.ceil(duration * SAMPLE_RATE))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b"\x00\x00" * frames)


def read_wav_duration(path: Path) -> float | None:
    try:
        with wave.open(str(path), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate <= 0:
                return None
            return float(frames) / float(rate)
    except Exception:
        return None

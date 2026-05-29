#!/usr/bin/env python3
import subprocess
import time
import numpy as np
import sounddevice as sd
import yaml
from faster_whisper import WhisperModel

with open("/home/spix/spidy-ai/config.yaml") as f:
    config = yaml.safe_load(f)

WAKE_WORDS  = config["wake"]["words"]
SAMPLE_RATE = 16000

print("[Wake] Loading Whisper tiny model...")
model = WhisperModel("tiny", device="cpu", compute_type="int8")
print("[Wake] Spidy ghost mode active — waiting for wake word...")

def listen_chunk() -> str:
    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32"
    ) as stream:
        audio, _ = stream.read(int(SAMPLE_RATE * 2.0))
        audio    = audio.flatten()
        rms      = float(np.sqrt(np.mean(audio ** 2)))
        if rms < 0.02:
            return ""
        segments, _ = model.transcribe(
            audio,
            beam_size=3,
            vad_filter=True
        )
        return " ".join([s.text for s in segments]).strip().lower()

def launch_spidy():
    print("[Wake] Wake word detected! Launching Spidy...")
    subprocess.Popen([
        "kitty",
        "--class", "spidy_ui",
        "-e", "/home/spix/spidy-ai/run_ui.sh"
    ])
    time.sleep(10)  # Pause listening while Spidy opens

if __name__ == "__main__":
    while True:
        try:
            text = listen_chunk()
            if text:
                print(f"[Wake] Heard: {text}")
                if any(w in text for w in WAKE_WORDS):
                    launch_spidy()
        except Exception as e:
            pass
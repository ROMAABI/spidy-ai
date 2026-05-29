import yaml
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

with open("config.yaml") as f:
    config = yaml.safe_load(f)

STT_CFG = config["stt"]

class STT:
    def __init__(self):
        print("[STT] Loading Whisper Small model...")
        self.model = WhisperModel(
            STT_CFG["model"],
            device=STT_CFG["device"],
            compute_type=STT_CFG["compute_type"]
        )
        self.sample_rate = STT_CFG["sample_rate"]
        print("[STT] Ready!")

    def listen(self) -> tuple[str, str]:
        audio = self._record_until_silence()
        if audio is None or len(audio) < self.sample_rate * 0.5:
            return "", "en"
        return self._transcribe(audio)

    def _record_until_silence(self) -> np.ndarray:
        # Import here to avoid circular import
        from core.tts import is_speaking

        chunk_duration   = 0.3
        silence_limit    = 1.5
        speech_threshold = 0.10
        max_duration     = 10.0
        chunk_samples    = int(self.sample_rate * chunk_duration)

        audio_chunks    = []
        silent_duration = 0.0
        speech_started  = False
        total_duration  = 0.0

        print("[STT] Listening...")

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32"
        ) as stream:
            while True:
                chunk, _ = stream.read(chunk_samples)
                chunk    = chunk.flatten()

                # Skip while TTS is speaking — prevents feedback loop
                if is_speaking():
                    silent_duration = 0.0
                    speech_started  = False
                    audio_chunks    = []
                    continue

                rms             = float(np.sqrt(np.mean(chunk ** 2)))
                total_duration += chunk_duration

                if rms > speech_threshold:
                    if not speech_started:
                        print("[STT] Speech detected!")
                    speech_started  = True
                    silent_duration = 0.0
                    audio_chunks.append(chunk)

                elif speech_started:
                    audio_chunks.append(chunk)
                    silent_duration += chunk_duration
                    if silent_duration >= silence_limit:
                        print("[STT] Silence detected — processing...")
                        break

                if total_duration >= max_duration:
                    print("[STT] Max duration reached — processing...")
                    break

        return np.concatenate(audio_chunks) if audio_chunks else None

    def _transcribe(self, audio: np.ndarray) -> tuple[str, str]:
        segments, info = self.model.transcribe(
            audio,
            beam_size=5,
            language=None,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=400,
                speech_pad_ms=200
            )
        )
        text = " ".join([seg.text.strip() for seg in segments]).strip()
        lang = info.language

        if text:
            print(f"[STT] [{lang.upper()}] {text}")

        return text, lang
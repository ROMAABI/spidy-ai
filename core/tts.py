"""
core/tts.py — Streaming conversational TTS

Architecture:
- Text chunks arrive incrementally via `feed_chunk(text, generation_id)`.
- A background worker pops from a thread-safe queue, generates WAV audio
  via gTTS → fffmpeg, normalises, and plays with sounddevice.
- Each new user message increments `generation_id` which cancels any
  in-flight TTS from the previous response and drains the queue.
- Debug timing logs are emitted at every stage.
"""
from __future__ import annotations

import os
import queue
import re
import subprocess
import threading
import time
from dataclasses import dataclass, field

import numpy as np
import sounddevice as sd
import yaml

with open(os.path.join(os.path.dirname(__file__), "..", "config.yaml")) as f:
    config = yaml.safe_load(f)

TTS_CFG = config.get("tts", {})
_volume_pct = TTS_CFG.get("volume", 100)
_tts_volume = max(0.0, min(1.0, _volume_pct / 100.0))

# ── Module-level state (shared across all callers) ──────────────

_current_generation = 0
_is_speaking = False
_queue_size = 0
_last_latency_ms = 0  # most recent TTS generate→playback latency

_tts_engine_type = "gTTS"
_tts_status = "idle"  # "generating" | "playing" | "idle"

# Locks for thread-safe access to globals
_gen_lock = threading.Lock()
_status_lock = threading.Lock()


# ── Public accessors (used by sidebar / debugging) ──────────────

def get_volume() -> float:
    return _tts_volume


def set_volume(pct: float) -> None:
    global _tts_volume
    _tts_volume = max(0.0, min(1.0, pct / 100.0))


def is_speaking() -> bool:
    return _is_speaking


def get_queue_size() -> int:
    return _queue_size


def get_last_latency_ms() -> int:
    return _last_latency_ms


def get_tts_status() -> str:
    return _tts_status


def get_tts_engine() -> str:
    return _tts_engine_type


# ── Text cleaning (stateless helpers) ───────────────────────────

# Comprehensive emoji ranges (Unicode 15+)
_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002500-\U00002BEF"  # CJK / misc — wide catch
    "\U00002702-\U000027B0"
    "\U000027C0-\U000027EF"
    "\U000024C2-\U0001F251"
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols Extended-A
    "\U00002600-\U000026FF"  # Misc symbols (weather, etc.)
    "\U0000FE00-\U0000FE0F"  # Variation Selectors
    "\U0000200D"            # Zero Width Joiner
    "\U00002B50"            # ⭐
    "\U00002764"            # ❤
    "\U0000203C"            # ‼
    "\U00002049"            # ⁉
    "\U00002300-\U000023FF"  # Misc Technical (⌚, etc.)
    "\U00002934-\U00002935"  # Arrows
    "\U000025AA-\U000025AB"  # Black/white squares
    "\U000025FB-\U000025FE"  # Medium squares
    "\U00002B1B-\U00002B1C"  # Black/white large squares
    "\U00002714-\U00002717"  # Check marks
    "\U00002764-\U000027EF"  # Dingbats cont.
    "\U0000FE0F"            # Variation selector
    "\U00002639"            # 🙁
    "\U00003297"            # 🈗
    "\U00003299"            # 🈙
    "\U0000329E"            # 🈞
    "\U0001F000-\U0001F02F"  # Mahjong
    "\U0001F030-\U0001F09F"  # Domino
    "\U0001F0A0-\U0001F0FF"  # Playing cards
    "\U0001F200-\U0001F2FF"  # Enclosed ideographic supplement
    "\U0001F004-\U0001F0CF"  # Misc
    "]+",
    re.UNICODE,
)

# Markdown / formatting artifacts to strip
_MARKDOWN_RE = re.compile(r"(`[^`]*`|```[\s\S]*?```|\*{1,3}|_{1,3}|~~|#{1,6}\s*|\[.*?\]\(.*?\)|>+\s*)")

# Multiple repeating punctuation -> single
_MULTI_PUNCT_RE = re.compile(r"([!?.]){2,}")
# Repeating characters (e.g. "nooooo" -> "no")
_REPEAT_CHAR_RE = re.compile(r"(.)\1{2,}")

# Symbol replacements (common)
_SYMBOL_MAP = str.maketrans({
    "%": " percent ",
    "&": " and ",
    "@": " at ",
    "+": " plus ",
    "#": " number ",
    "~": " tilde ",
    "|": " ",
    "•": " ",
    "·": " ",
    "●": " ",
    "○": " ",
    "◆": " ",
    "◇": " ",
    "■": " ",
    "□": " ",
    "▸": " ",
    "▹": " ",
    "►": " ",
    "▪": " ",
    "▫": " ",
    "▶": " ",
    "∆": " ",
    "→": " ",
    "←": " ",
    "↑": " ",
    "↓": " ",
    "↔": " ",
    "➜": " ",
    "=": " equals ",
    "✓": " ",
    "✗": " ",
    "✕": " ",
    "✔": " ",
    "✖": " ",
})


def clean_text(text: str) -> str:
    """Remove / normalise content unsuitable for TTS.

    - Strips emojis, markdown, decorative characters, ASCII art,
      UI borders, terminal formatting.
    - Collapses multiple punctuation to one.
    - Replaces common symbols with spoken words.
    """
    # 1. Strip markdown code blocks and inline code
    text = _MARKDOWN_RE.sub("", text)

    # 2. Strip emojis and wide symbols
    text = _EMOJI_RE.sub("", text)

    # 3. Replace common symbols
    text = text.translate(_SYMBOL_MAP)

    # 4. Collapse multiple punctuation
    text = _MULTI_PUNCT_RE.sub(r"\1", text)

    # 5. Normalise whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # 6. Strip lines that are purely decorative (borders, rulers, etc.)
    lines = text.split("\n")
    filtered = []
    for line in lines:
        stripped = line.strip()
        # Skip lines that are only punctuation/dashes/equals/asterisks/borders
        if stripped and re.match(r"^[\s\-\=\*\_\#\:\|\.\>\/\\\(\)\[\]\{\}\~\+\@]+$", stripped):
            continue
        filtered.append(stripped)
    text = " ".join(filtered).strip()

    # 7. Final whitespace squeeze
    text = re.sub(r"\s+", " ", text).strip()

    return text


# ── Sentence splitting (for streaming) ─────────────────────────

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[\"'(]?[A-Z0-9])")
_MAX_CHUNK_CHARS = 300  # max chars before force-splitting at word boundary
_MIN_CHUNK_CHARS = 15   # minimum chars before we consider a boundary valid


def split_sentences(text: str) -> list[str]:
    """Split cleaned text into speakable chunks (sentences + forced splits)."""
    if not text:
        return []

    text = clean_text(text)
    if not text:
        return []

    # Split on sentence boundaries first
    raw_parts = _SENTENCE_BOUNDARY.split(text)
    chunks: list[str] = []

    for part in raw_parts:
        part = part.strip()
        if not part:
            continue

        if len(part) <= _MAX_CHUNK_CHARS:
            chunks.append(part)
        else:
            # Force-split at word boundaries
            words = part.split()
            current: list[str] = []
            for w in words:
                current.append(w)
                total = len(" ".join(current))
                if total >= _MAX_CHUNK_CHARS:
                    chunks.append(" ".join(current))
                    current = []
            if current:
                chunks.append(" ".join(current))

    return [c for c in chunks if len(c) >= _MIN_CHUNK_CHARS or (len(c) > 2 and c[-1] in ".!?")]


# ── Streaming TTS engine ────────────────────────────────────────

@dataclass
class _QueueItem:
    text: str
    generation: int
    enqueued_at: float = field(default_factory=time.perf_counter)


class TTS:
    """Streaming TTS engine with sentence-level chunking and background playback.

    Usage:
        tts = TTS()
        gen = tts.new_generation()    # new conversation turn
        tts.feed_chunk("Hello world", gen)
        tts.feed_chunk("How are you?", gen)
        ...
        tts.finish_generation(gen)
        tts.cancel()                  # on new user message
    """

    def __init__(self):
        self._queue: queue.Queue[_QueueItem | None] = queue.Queue()
        self._lock = threading.Lock()
        self._wake_event = threading.Event()
        self._worker = threading.Thread(target=self._worker_loop, daemon=True, name="tts-worker")
        self._worker.start()

    # ── Public API ──────────────────────────────────────────────

    def new_generation(self) -> int:
        """Start a new TTS generation (call on each user message)."""
        global _current_generation, _is_speaking, _queue_size, _tts_status
        with _gen_lock:
            _current_generation += 1
            gen = _current_generation
        # Cancel any in-flight speech
        sd.stop()
        with _status_lock:
            _is_speaking = False
            _tts_status = "idle"
        # Drain the queue
        drained = 0
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                drained += 1
            except queue.Empty:
                break
        with _gen_lock:
            _queue_size = 0
        print(f"[TTS] Generation {gen} started (drained {drained} stale items)")
        return gen

    def feed_chunk(self, text: str, generation: int) -> None:
        """Enqueue a cleaned text chunk for TTS generation and playback.

        If *generation* is stale (canceled), the chunk is silently dropped.
        """
        if not text or len(text) < 2:
            return
        with _gen_lock:
            if generation != _current_generation:
                # Stale generation — discard
                return
        item = _QueueItem(text=text, generation=generation)
        self._queue.put(item)
        with _gen_lock:
            global _queue_size
            _queue_size = self._queue.qsize()
        t_now = time.perf_counter()
        print(f"[TTS] Chunk queued: \"{text[:60]}...\" ({len(text)} chars) at {t_now:.3f}")
        self._wake_event.set()

    def finish_generation(self, generation: int) -> None:
        """Optional: signal that no more chunks will arrive for *generation*.
        Currently a no-op (the queue handles it naturally).
        """
        pass

    def cancel(self) -> None:
        """Immediate stop — stops playback, drains queue."""
        sd.stop()
        with _gen_lock:
            global _current_generation
            _current_generation += 1  # make all in-flight items stale
        with _status_lock:
            global _is_speaking, _tts_status
            _is_speaking = False
            _tts_status = "idle"
        drained = 0
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                drained += 1
            except queue.Empty:
                break
        with _gen_lock:
            global _queue_size
            _queue_size = 0
        print(f"[TTS] Cancelled — drained {drained} pending items")

    def get_speaking(self) -> bool:
        return _is_speaking

    def get_queue_size(self) -> int:
        return _queue_size

    # ── Legacy-compatible API ────────────────────────────────────

    def speak(self, text: str, lang: str = "en") -> None:
        """Backward-compatible synchronous speak.

        Internally creates a one-shot generation, cleans + splits the text,
        and processes chunks in-line (blocking).
        """
        gen = self.new_generation()
        chunks = split_sentences(text)
        if not chunks:
            return
        for chunk in chunks:
            cleaned = clean_text(chunk)
            if cleaned:
                item = _QueueItem(text=cleaned, generation=gen)
                self._process_item(item)
        self.finish_generation(gen)

    def speak_async(self, text: str, lang: str = "en") -> None:
        """Backward-compatible asynchronous speak.

        Splits text into sentence chunks and enqueues them for the
        background worker.  Returns immediately.
        """
        gen = self.new_generation()
        chunks = split_sentences(text)
        if not chunks:
            return
        for chunk in chunks:
            cleaned = clean_text(chunk)
            if cleaned:
                self.feed_chunk(cleaned, gen)
        self.finish_generation(gen)

    # ── Private worker ──────────────────────────────────────────

    def _worker_loop(self) -> None:
        """Background thread: pop items from queue, generate, play."""
        global _is_speaking, _queue_size, _last_latency_ms, _tts_status
        while True:
            # Wait for work (blocking)
            self._wake_event.wait(timeout=30)
            self._wake_event.clear()

            try:
                item: _QueueItem | None = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue
            if item is None:
                continue

            # Check generation freshness
            with _gen_lock:
                if item.generation != _current_generation:
                    with _gen_lock:
                        _queue_size = self._queue.qsize()
                    continue

            with _status_lock:
                _is_speaking = True
                _tts_status = "generating"

            # Generate and play
            self._process_item(item)

            with _gen_lock:
                _queue_size = self._queue.qsize()
            if self._queue.qsize() == 0:
                with _status_lock:
                    _is_speaking = False
                    _tts_status = "idle"

    def _process_item(self, item: _QueueItem) -> None:
        """Generate audio for *item* and play it, checking cancellation."""
        global _last_latency_ms, _tts_status, _is_speaking

        # ── Phase 1: generate audio via gTTS → ffmpeg ──
        text = clean_text(item.text)
        if not text or len(text) < 2:
            return

        with _status_lock:
            _tts_status = "generating"

        t_gen_start = time.perf_counter()
        audio, sr = self._generate_audio(text)
        t_gen_done = time.perf_counter()
        gen_ms = (t_gen_done - t_gen_start) * 1000

        if audio is None:
            print(f"[TTS] Generation failed for: \"{text[:50]}...\"")
            return

        # Check cancellation before playing
        with _gen_lock:
            if item.generation != _current_generation:
                print(f"[TTS] Generation {item.generation} cancelled before playback")
                return

        # ── Phase 2: play audio ──
        with _status_lock:
            _tts_status = "playing"

        t_play_start = time.perf_counter()
        try:
            sd.play(audio, sr)
            # Poll for cancellation during playback
            played = 0
            total_frames = len(audio)
            while played < total_frames:
                sd.sleep(50)  # 50ms polling
                played = sd.get_stream().time * sr if sd.get_stream() else total_frames
                with _gen_lock:
                    if item.generation != _current_generation:
                        sd.stop()
                        print(f"[TTS] Playback interrupted — generation {item.generation} stale")
                        return
            sd.wait()
        except Exception as e:
            print(f"[TTS] Playback error: {e}")
            return

        t_play_done = time.perf_counter()
        play_ms = (t_play_done - t_play_start) * 1000
        total_ms = (t_play_done - t_gen_start) * 1000

        _last_latency_ms = int(total_ms)
        elapsed = t_play_done - item.enqueued_at
        print(
            f"[TTS] Chunk done: gen={item.generation} "
            f"text=\"{text[:40]}...\" "
            f"generate={gen_ms:.0f}ms "
            f"playback={play_ms:.0f}ms "
            f"total={total_ms:.0f}ms "
            f"queue_latency={elapsed*1000:.0f}ms"
        )

    def _generate_audio(self, text: str) -> tuple[np.ndarray | None, int]:
        """Run gTTS → ffmpeg pipeline, return (audio_float32, sample_rate)."""
        try:
            from gtts import gTTS

            tts = gTTS(text=text, lang="en", slow=False)
            tmp = f"/tmp/spidy_tts_{int(time.time()*1000)}_{id(text)}.mp3"
            tts.save(tmp)

            wav_path = tmp.replace(".mp3", ".wav")
            proc = subprocess.run(
                [
                    "ffmpeg", "-y", "-i", tmp,
                    "-ar", "22050", "-ac", "1",
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                    wav_path,
                ],
                capture_output=True,
            )

            if proc.returncode == 0:
                import wave
                with wave.open(wav_path, "rb") as w:
                    sr = w.getframerate()
                    audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
                    audio = audio.astype(np.float32) / 32768.0
            else:
                # Fallback: pipe through ffmpeg
                proc = subprocess.run(
                    [
                        "ffmpeg", "-y", "-i", tmp,
                        "-ar", "22050", "-ac", "1",
                        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                        "-f", "wav", "-",
                    ],
                    capture_output=True,
                )
                if proc.returncode != 0:
                    print(f"[TTS] ffmpeg error: {proc.stderr.decode()[:200]}")
                    # Cleanup tmp
                    try:
                        os.remove(tmp)
                    except OSError:
                        pass
                    return None, 0
                audio, sr = self._read_wav_from_bytes(proc.stdout)

            # Cleanup tmp files
            try:
                os.remove(tmp)
            except OSError:
                pass
            try:
                os.remove(wav_path)
            except OSError:
                pass

            # Normalise and apply volume
            audio = _trim_silence(audio)
            audio = _normalize(audio, target_peak=0.95)
            audio = np.clip(audio * _tts_volume, -1.0, 1.0)

            return audio, sr

        except Exception as e:
            print(f"[TTS] Google TTS error: {e}")
            return None, 0

    @staticmethod
    def _read_wav_from_bytes(data: bytes) -> tuple[np.ndarray, int]:
        import io
        import wave
        with wave.open(io.BytesIO(data), "rb") as w:
            sr = w.getframerate()
            frames = w.readframes(w.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        return audio, sr


# ── Legacy compatibility wrappers (for non-streaming callers) ───

_legacy_tts: TTS | None = None


def _get_tts() -> TTS:
    global _legacy_tts
    if _legacy_tts is None:
        _legacy_tts = TTS()
    return _legacy_tts


def speak_async(text: str, lang: str = "en") -> None:
    """Legacy: speak full text (blocking generation, then play)."""
    engine = _get_tts()
    gen = engine.new_generation()
    chunks = split_sentences(text)
    if not chunks:
        return
    for chunk in chunks:
        engine.feed_chunk(chunk, gen)
    engine.finish_generation(gen)


def cancel_speech() -> None:
    """Cancel any in-progress TTS (streaming or legacy)."""
    engine = _get_tts()
    engine.cancel()


def speak_stream(text: str, lang: str = "en") -> None:
    """Convenience: clean, split, and enqueue an entire response as streaming chunks."""
    speak_async(text, lang)


# ── Audio helpers (unchanged) ──────────────────────────────────

def _trim_silence(audio: np.ndarray, threshold: float = 0.01) -> np.ndarray:
    abs_audio = np.abs(audio)
    non_silent = np.where(abs_audio > threshold)[0]
    if len(non_silent) == 0:
        return audio
    start = max(0, non_silent[0] - 500)
    end = min(len(audio), non_silent[-1] + 500)
    return audio[start:end]


def _normalize(audio: np.ndarray, target_peak: float = 0.95) -> np.ndarray:
    peak = np.max(np.abs(audio))
    if peak < 1e-6:
        return audio
    return audio * (target_peak / peak)

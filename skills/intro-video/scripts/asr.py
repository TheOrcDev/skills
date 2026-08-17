#!/usr/bin/env python3
"""Word-level ASR timestamps for Remotion captions.

Uses sherpa-onnx + a zipformer model from GitHub release assets.
Do not estimate caption times — run this.

  python3 asr.py voice.wav --fps 30 --out captions.json
  python3 asr.py reel.mp4 --fps 30
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import wave
from pathlib import Path

MODEL_URL = (
    "https://github.com/k2-fsa/sherpa-onnx/releases/download/"
    "asr-models/sherpa-onnx-zipformer-en-2023-06-26.tar.bz2"
)
MODEL_DIR_NAME = "sherpa-onnx-zipformer-en-2023-06-26"
DEFAULT_CACHE = Path.home() / ".cache" / "intro-video"


def die(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def ensure_deps() -> None:
    try:
        import numpy  # noqa: F401
        import sherpa_onnx  # noqa: F401
    except ImportError:
        die(
            "Missing ASR deps. Install with:\n"
            "  python3 -m pip install sherpa-onnx numpy"
        )
    if shutil.which("ffmpeg") is None:
        die("ffmpeg not found on PATH. Install ffmpeg and retry.")


def download_model(cache: Path) -> Path:
    dest = cache / MODEL_DIR_NAME
    if (dest / "tokens.txt").exists():
        return dest

    cache.mkdir(parents=True, exist_ok=True)
    archive = cache / f"{MODEL_DIR_NAME}.tar.bz2"
    print(f"Downloading {MODEL_URL}", file=sys.stderr)
    urllib.request.urlretrieve(MODEL_URL, archive)
    print(f"Extracting {archive}", file=sys.stderr)
    with tarfile.open(archive, "r:bz2") as tar:
        try:
            tar.extractall(cache, filter="data")
        except TypeError:
            tar.extractall(cache)
    archive.unlink(missing_ok=True)
    if not (dest / "tokens.txt").exists():
        die(f"Model extract failed — tokens.txt missing in {dest}")
    return dest


def first_match(model_dir: Path, *patterns: str) -> Path:
    hits: list[Path] = []
    for pattern in patterns:
        hits.extend(model_dir.glob(pattern))
    if not hits:
        die(f"No file matching {patterns} in {model_dir}")
    hits.sort(key=lambda p: (".int8." in p.name, p.name))
    return hits[0]


def to_wav(src: Path, dst: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(dst),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        die(f"ffmpeg failed:\n{proc.stderr.strip() or proc.stdout.strip()}")


def read_wav(path: Path) -> tuple[list[float], int]:
    import numpy as np

    with wave.open(str(path), "rb") as wf:
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
            die(f"Expected 16-bit mono WAV, got {path}")
        samples = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
        return (samples.astype("float32") / 32768.0).tolist(), wf.getframerate()


def words_from_tokens(
    tokens: list[str], timestamps: list[float], duration: float
) -> list[dict]:
    words: list[dict] = []
    current = ""
    start: float | None = None

    def flush(end: float) -> None:
        nonlocal current, start
        text = current.replace("▁", "").strip()
        if text and start is not None:
            words.append(
                {
                    "word": text,
                    "start": round(start, 3),
                    "end": round(max(end, start), 3),
                }
            )
        current = ""
        start = None

    for token, ts in zip(tokens, timestamps):
        new_word = token.startswith("▁") or token.startswith(" ")
        if new_word and current:
            flush(ts)
        if start is None:
            start = ts
        current += token
    if current:
        flush(duration)
    return words


def transcribe(wav: Path, model_dir: Path) -> dict:
    import sherpa_onnx

    recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=str(first_match(model_dir, "encoder*.onnx", "encoder*.int8.onnx")),
        decoder=str(first_match(model_dir, "decoder*.onnx", "decoder*.int8.onnx")),
        joiner=str(first_match(model_dir, "joiner*.onnx", "joiner*.int8.onnx")),
        tokens=str(model_dir / "tokens.txt"),
        num_threads=2,
        sample_rate=16000,
        feature_dim=80,
        decoding_method="greedy_search",
    )
    samples, sample_rate = read_wav(wav)
    duration = len(samples) / float(sample_rate)
    stream = recognizer.create_stream()
    stream.accept_waveform(sample_rate, samples)
    recognizer.decode_stream(stream)
    result = stream.result
    tokens = list(result.tokens or [])
    timestamps = [float(t) for t in (result.timestamps or [])]
    if len(timestamps) != len(tokens):
        timestamps = timestamps[: len(tokens)] + [duration] * (
            len(tokens) - len(timestamps)
        )
    return {
        "text": result.text or "",
        "duration": round(duration, 3),
        "words": words_from_tokens(tokens, timestamps, duration),
    }


def add_frames(payload: dict, fps: float) -> dict:
    for word in payload["words"]:
        word["start_frame"] = int(round(word["start"] * fps))
        word["end_frame"] = max(
            word["start_frame"] + 1, int(round(word["end"] * fps))
        )
    payload["fps"] = fps
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Word-level ASR timestamps. Use these times for captions — do not estimate."
    )
    parser.add_argument("media", help="Audio or video file with the voiceover")
    parser.add_argument("--fps", type=float, default=30, help="Composition fps (default 30)")
    parser.add_argument(
        "--out",
        help="Write JSON here. Default: <stem>.asr.json next to the input.",
    )
    parser.add_argument(
        "--model-dir",
        help="Existing extracted zipformer directory. Default: download to ~/.cache/intro-video",
    )
    parser.add_argument(
        "--cache",
        default=str(DEFAULT_CACHE),
        help="Where to cache the downloaded model",
    )
    args = parser.parse_args()

    ensure_deps()
    media = Path(args.media).expanduser().resolve()
    if not media.exists():
        die(f"File not found: {media}")

    model_dir = (
        Path(args.model_dir).expanduser().resolve()
        if args.model_dir
        else download_model(Path(args.cache).expanduser())
    )
    if not (model_dir / "tokens.txt").exists():
        die(f"tokens.txt not found in {model_dir}")

    with tempfile.TemporaryDirectory(prefix="intro-video-asr-") as tmp:
        wav = Path(tmp) / "voice.wav"
        to_wav(media, wav)
        payload = transcribe(wav, model_dir)

    payload["source"] = str(media)
    add_frames(payload, args.fps)

    out = (
        Path(args.out).expanduser()
        if args.out
        else media.with_name(media.stem + ".asr.json")
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(out)
    print(payload["text"], file=sys.stderr)


if __name__ == "__main__":
    main()

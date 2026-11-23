#!/usr/bin/env python3
"""Word-level timings for cueing the drawing.

whisper.cpp word offsets drift (up to ~1s late) over a long file, so this
transcribes overlapping 14s windows and keeps each word from the window where
it sits away from the edges. Times are absolute seconds in the video.

Usage: words.py VIDEO [OUT.json]   (default OUT: words.json next to the cwd)
Env:   WHISPER_MODEL  ggml model path (default ~/.cache/whisper-cpp/ggml-large-v3-turbo-q5_0.bin)
       WHISPER_BIN    whisper-cli binary (default whisper-cli)
Prints the transcript as "12.34:word" so cues can be read straight off it.
"""
import json
import os
import subprocess
import sys
import tempfile

if len(sys.argv) < 2:
    sys.exit(__doc__)
video = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else "words.json"
model = os.path.expanduser(os.environ.get("WHISPER_MODEL", "~/.cache/whisper-cpp/ggml-large-v3-turbo-q5_0.bin"))
binary = os.environ.get("WHISPER_BIN", "whisper-cli")
WIN, STEP, EDGE = 14.0, 12.0, 1.0

tmp = tempfile.mkdtemp()
wav = os.path.join(tmp, "audio.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-ar", "16000", "-ac", "1", wav], check=True)
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav]))

words = []
start = 0.0
while start < dur:
    clip = os.path.join(tmp, f"c{int(start)}.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", str(WIN), "-i", wav, clip], check=True)
    base = os.path.join(tmp, f"w{int(start)}")
    subprocess.run([binary, "-m", model, "-f", clip, "-ml", "1", "-sow", "-oj", "-of", base, "-np"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    lo = start + (EDGE if start > 0 else 0)
    hi = start + STEP + EDGE if start + WIN < dur else dur + 1
    for seg in json.load(open(base + ".json"))["transcription"]:
        text = seg["text"].strip()
        t0 = start + seg["offsets"]["from"] / 1000
        t1 = start + seg["offsets"]["to"] / 1000
        if text and lo <= t0 < hi:
            words.append({"t": round(t0, 2), "end": round(t1, 2), "word": text})
    start += STEP

words.sort(key=lambda w: w["t"])
json.dump(words, open(out, "w"), indent=1)
print(" ".join(f"{w['t']:.2f}:{w['word']}" for w in words))
print(f"\n{len(words)} words -> {out}", file=sys.stderr)

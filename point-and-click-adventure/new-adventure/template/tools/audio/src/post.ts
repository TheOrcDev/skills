// `post` (audio-pipeline.md §4.5): a voice master becomes the game's line. It
// is trimmed to the speech plus a little air, brought to the voice loudness,
// and written as 24 kHz mono 16-bit WAV into the Godot project, which imports
// it as QOA, so no WAV ships. Its loudness envelope goes into
// the table the Voice autoload reads. ffmpeg decodes the master and measures
// loudness with its EBU R128 scanner; everything else happens here.

import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { canonical, sha256 } from "./hash";

/** Starting values, tuned in Past's mix pass. */
export const POST = {
  rate: 24000,
  /** Air kept before the first speech and after the last, padded with silence if the master has less. */
  leadMs: 80,
  tailMs: 200,
  /** A 10 ms window louder than this is speech, for trimming. */
  speechDb: -50,
  /** Fades at the cut points, so a cut through breath noise never clicks. */
  fadeMs: 5,
  targetLufs: -18,
  peakDbtp: -1,
  /** Envelope values a second (technical-plan.md §6.5). */
  envelopeRate: 30,
  /** A window's RMS maps from floorDb (0) to ceilingDb (1). */
  floorDb: -45,
  ceilingDb: -12,
};

export type PostSettings = typeof POST;

/** What `post` made of one master, kept in audio-source/voice/post.json. */
export interface PostEntry {
  /** sha256 of the master's bytes. */
  source: string;
  /** Hash of the settings it was made with: a change remakes every line. */
  settings: string;
  seconds: number;
  /** Integrated loudness and true peak as measured, before the gain. */
  measured: { integrated: number; truePeak: number };
  gainDb: number;
  /** The envelope's bytes (0–255), base64. */
  envelope: string;
}

export function settingsHash(settings: PostSettings = POST): string {
  return sha256(canonical(settings));
}

export function fileHash(path: string): string {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

function rmsDb(samples: Float32Array, start: number, end: number): number {
  let sum = 0;
  for (let i = start; i < end; i++) sum += samples[i] * samples[i];
  return 10 * Math.log10(sum / Math.max(1, end - start) + 1e-20);
}

/** The first and last sample of speech (end exclusive), by 10 ms windows; null when the master is all silence. */
export function speechSpan(samples: Float32Array, rate: number, settings: PostSettings = POST): { start: number; end: number } | null {
  const window = Math.round(rate / 100);
  let start = -1;
  let end = -1;
  for (let at = 0; at < samples.length; at += window) {
    const stop = Math.min(samples.length, at + window);
    if (rmsDb(samples, at, stop) > settings.speechDb) {
      if (start < 0) start = at;
      end = stop;
    }
  }
  return start < 0 ? null : { start, end };
}

/** The speech with exactly leadMs before it and tailMs after, faded at the cuts. */
export function trim(samples: Float32Array, rate: number, settings: PostSettings = POST): Float32Array {
  const span = speechSpan(samples, rate, settings);
  if (!span) throw new Error("the master is silent");
  const lead = Math.round((rate * settings.leadMs) / 1000);
  const tail = Math.round((rate * settings.tailMs) / 1000);
  const out = new Float32Array(lead + (span.end - span.start) + tail);
  const from = Math.max(0, span.start - lead);
  const to = Math.min(samples.length, span.end + tail);
  out.set(samples.subarray(from, to), lead - (span.start - from));
  const fade = Math.round((rate * settings.fadeMs) / 1000);
  const first = lead - (span.start - from);
  const last = first + (to - from);
  for (let i = 0; i < fade; i++) {
    const g = i / fade;
    if (first + i < out.length) out[first + i] *= g;
    if (last - 1 - i >= 0) out[last - 1 - i] *= g;
  }
  return out;
}

/** The gain that brings a line to the target loudness without its true peak passing the ceiling. A line too short for a loudness reading is set by its peak. */
export function gainDb(measured: { integrated: number; truePeak: number }, settings: PostSettings = POST): number {
  const toPeak = settings.peakDbtp - measured.truePeak;
  if (!Number.isFinite(measured.integrated) || measured.integrated <= -70) return toPeak;
  return Math.min(settings.targetLufs - measured.integrated, toPeak);
}

export function applyGain(samples: Float32Array, db: number): Float32Array {
  const factor = 10 ** (db / 20);
  return samples.map((s) => s * factor);
}

/** envelopeRate loudness values a second, 0–255: window i covers [i, i + 1) / envelopeRate seconds. */
export function envelope(samples: Float32Array, rate: number, settings: PostSettings = POST): Uint8Array {
  const window = rate / settings.envelopeRate;
  const out = new Uint8Array(Math.ceil(samples.length / window));
  for (let i = 0; i < out.length; i++) {
    const db = rmsDb(samples, Math.round(i * window), Math.min(samples.length, Math.round((i + 1) * window)));
    const t = (db - settings.floorDb) / (settings.ceilingDb - settings.floorDb);
    out[i] = Math.round(Math.min(1, Math.max(0, t)) * 255);
  }
  return out;
}

/** Mono 16-bit PCM WAV. */
export function wavBytes(samples: Float32Array, rate: number): Uint8Array {
  const bytes = new Uint8Array(44 + samples.length * 2);
  const view = new DataView(bytes.buffer);
  const text = (at: number, s: string) => [...s].forEach((c, i) => view.setUint8(at + i, c.charCodeAt(0)));
  text(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  text(8, "WAVE");
  text(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // mono
  view.setUint32(24, rate, true);
  view.setUint32(28, rate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  text(36, "data");
  view.setUint32(40, samples.length * 2, true);
  samples.forEach((s, i) => view.setInt16(44 + i * 2, Math.round(Math.max(-1, Math.min(1, s)) * 32767), true));
  return bytes;
}

/** The master as mono float samples at `rate`, decoded by ffmpeg. */
export function decode(path: string, rate: number): Float32Array {
  const result = Bun.spawnSync(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", String(rate), "-f", "f32le", "-"]);
  if (result.exitCode !== 0) throw new Error(`ffmpeg could not read ${path}: ${result.stderr.toString().trim()}`);
  const out = result.stdout;
  return new Float32Array(out.buffer.slice(out.byteOffset, out.byteOffset + out.byteLength));
}

/** Integrated loudness (LUFS) and true peak (dBTP), from ffmpeg's EBU R128 scanner. */
export function measure(samples: Float32Array, rate: number): { integrated: number; truePeak: number } {
  const result = Bun.spawnSync(
    ["ffmpeg", "-hide_banner", "-nostats", "-f", "f32le", "-ar", String(rate), "-ac", "1", "-i", "-", "-af", "ebur128=peak=true:framelog=quiet", "-f", "null", "-"],
    { stdin: new Uint8Array(samples.buffer, samples.byteOffset, samples.byteLength) },
  );
  const log = result.stderr.toString();
  const integrated = log.match(/I:\s+(-?[\d.]+|-inf) LUFS/)?.[1];
  const truePeak = log.match(/True peak:\s+Peak:\s+(-?[\d.]+|-inf) dBFS/)?.[1];
  if (result.exitCode !== 0 || integrated === undefined || truePeak === undefined) throw new Error(`ffmpeg could not measure loudness: ${log.slice(-400)}`);
  const value = (text: string) => (text === "-inf" ? -Infinity : Number(text));
  return { integrated: value(integrated), truePeak: value(truePeak) };
}

/** Posts the master at `master` to the WAV at `out`. */
export function postLine(master: string, out: string, settings: PostSettings = POST): PostEntry {
  const source = fileHash(master);
  const trimmed = trim(decode(master, settings.rate), settings.rate, settings);
  const measured = measure(trimmed, settings.rate);
  const gain = gainDb(measured, settings);
  const line = applyGain(trimmed, gain);
  writeFileSync(out, wavBytes(line, settings.rate));
  return {
    source,
    settings: settingsHash(settings),
    seconds: Number((line.length / settings.rate).toFixed(3)),
    measured,
    gainDb: Number(gain.toFixed(2)),
    envelope: Buffer.from(envelope(line, settings.rate, settings)).toString("base64"),
  };
}

/** The GDScript table the Voice autoload reads: RATE, and LINES from each line ID to its envelope. */
export function envelopeTable(entries: Record<string, PostEntry>, settings: PostSettings = POST): string {
  const ids = Object.keys(entries).sort();
  return [
    "# Written by `bun tools/audio/run.ts post` (audio-pipeline.md §4.5); don't edit.",
    "# RATE is values a second. LINES maps each line ID to its loudness envelope:",
    "# base64 bytes, 0 silent to 255 loudest.",
    "",
    `const RATE := ${settings.envelopeRate}`,
    "const LINES := {",
    ...ids.map((id) => `\t&"${id}": "${entries[id].envelope}",`),
    "}",
    "",
  ].join("\n");
}

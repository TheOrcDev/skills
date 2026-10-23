import { expect, test } from "bun:test";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { decode, envelope, envelopeTable, gainDb, measure, POST, postLine, speechSpan, trim, wavBytes, type PostEntry } from "../src/post";

const RATE = 24000;

/** `before` s of silence, `tone` s of a 220 Hz tone at `amplitude`, then `after` s of silence. */
function clip(before: number, tone: number, after: number, amplitude = 0.3, rate = RATE): Float32Array {
  const out = new Float32Array(Math.round((before + tone + after) * rate));
  const start = Math.round(before * rate);
  for (let i = 0; i < Math.round(tone * rate); i++) out[start + i] = Math.sin((i * 2 * Math.PI * 220) / rate) * amplitude;
  return out;
}

test("trimming keeps the speech with 80 ms before and 200 ms after", () => {
  const out = trim(clip(0.5, 1.0, 0.5), RATE);
  expect(out.length / RATE).toBeCloseTo(0.08 + 1.0 + 0.2, 2);
  const lead = out.subarray(0, Math.round(0.07 * RATE));
  expect(Math.max(...lead.map(Math.abs))).toBe(0);
  expect(Math.max(...out.subarray(Math.round(0.5 * RATE), Math.round(0.6 * RATE)).map(Math.abs))).toBeCloseTo(0.3, 2);
});

test("a master with less air is padded, so every line has the same lead", () => {
  const out = trim(clip(0, 1.0, 0.05), RATE);
  expect(out.length / RATE).toBeCloseTo(0.08 + 1.0 + 0.2, 2);
  expect(speechSpan(out, RATE)?.start).toBe(Math.round(0.08 * RATE));
});

test("a silent master is refused", () => {
  expect(() => trim(new Float32Array(RATE), RATE)).toThrow("silent");
});

test("the gain reaches the target loudness unless the peak would pass -1 dBTP", () => {
  expect(gainDb({ integrated: -24, truePeak: -12 })).toBe(6);
  expect(gainDb({ integrated: -24, truePeak: -4 })).toBe(3);
  expect(gainDb({ integrated: -70, truePeak: -10 }), "too short to read: set by the peak").toBe(9);
  expect(gainDb({ integrated: -Infinity, truePeak: -10 })).toBe(9);
});

test("the envelope gives 30 values a second, from silence at 0 to loud at 255", () => {
  const rate = RATE;
  const samples = new Float32Array(rate);
  // The second half: RMS -12 dBFS, a sine of amplitude 10^(-12/20) * sqrt(2).
  const amplitude = 10 ** (-12 / 20) * Math.SQRT2;
  for (let i = rate / 2; i < rate; i++) samples[i] = Math.sin((i * 2 * Math.PI * 300) / rate) * amplitude;
  const values = envelope(samples, rate);
  expect(values.length).toBe(30);
  expect(values[0]).toBe(0);
  expect(values[29]).toBeGreaterThanOrEqual(253);
  // Halfway between floor and ceiling in dB is half scale.
  const mid = new Float32Array(rate).map((_, i) => Math.sin((i * 2 * Math.PI * 300) / rate) * 10 ** (((POST.floorDb + POST.ceilingDb) / 2) / 20) * Math.SQRT2);
  expect(envelope(mid, rate)[10]).toBeCloseTo(128, -1);
});

test("the WAV is mono 16-bit PCM at the given rate", () => {
  const bytes = wavBytes(new Float32Array([0, 0.5, -1, 2]), RATE);
  const view = new DataView(bytes.buffer);
  expect(new TextDecoder().decode(bytes.subarray(0, 4))).toBe("RIFF");
  expect(view.getUint16(22, true)).toBe(1);
  expect(view.getUint32(24, true)).toBe(RATE);
  expect(view.getUint16(34, true)).toBe(16);
  expect([0, 1, 2, 3].map((i) => view.getInt16(44 + i * 2, true))).toEqual([0, 16384, -32767, 32767]);
});

test("the envelope table is GDScript, sorted by line ID", () => {
  const entry = (envelope: string) => ({ envelope }) as PostEntry;
  const table = envelopeTable({ B_1: entry("AAE="), A_1: entry("/w==") });
  expect(table).toContain("const RATE := 30\n");
  expect(table).toContain('const LINES := {\n\t&"A_1": "/w==",\n\t&"B_1": "AAE=",\n}\n');
});

const hasFfmpeg = Bun.spawnSync(["which", "ffmpeg"]).exitCode === 0;

test.skipIf(!hasFfmpeg)("a quiet master comes out at -18 LUFS, trimmed and at 24 kHz", () => {
  const dir = mkdtempSync(join(tmpdir(), "past-post-"));
  try {
    const master = join(dir, "LINE_1.wav");
    writeFileSync(master, wavBytes(clip(0.4, 1.5, 0.6, 0.05, 44100), 44100));
    const out = join(dir, "out.wav");
    const entry = postLine(master, out);
    expect(entry.seconds).toBeCloseTo(0.08 + 1.5 + 0.2, 1);
    expect(entry.gainDb).toBeGreaterThan(0);
    expect(new DataView(readFileSync(out).buffer).getUint32(24, true)).toBe(24000);
    const again = measure(decode(out, 24000), 24000);
    expect(Math.abs(again.integrated - POST.targetLufs)).toBeLessThan(0.3);
    expect(again.truePeak).toBeLessThanOrEqual(POST.peakDbtp + 0.1);
    expect(Buffer.from(entry.envelope, "base64").length).toBe(Math.ceil(entry.seconds * 30));
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

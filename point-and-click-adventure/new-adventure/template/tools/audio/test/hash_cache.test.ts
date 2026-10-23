import { expect, test } from "bun:test";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { RequestCache } from "../src/cache";
import { canonical, requestHash } from "../src/hash";

test("the request hash ignores key order and changes with the text", () => {
  const a = requestHash({ endpoint: "tts", model: "v3", voice: "abc", settings: { stability: 0.5, style: 0.1 }, text: "Hi." });
  const b = requestHash({ text: "Hi.", voice: "abc", endpoint: "tts", settings: { style: 0.1, stability: 0.5 }, model: "v3" });
  expect(a).toBe(b);
  expect(requestHash({ endpoint: "tts", model: "v3", voice: "abc", text: "Hi!" })).not.toBe(a);
  expect(canonical({ b: 1, a: [2, { d: 3, c: 4 }] })).toBe('{"a":[2,{"c":4,"d":3}],"b":1}');
});

test("the same hash never calls twice unless forced", async () => {
  const dir = mkdtempSync(join(tmpdir(), "past-cache-"));
  try {
    const cache = new RequestCache(dir);
    let calls = 0;
    const call = async () => {
      calls++;
      return new Uint8Array([calls]);
    };
    expect((await cache.get("h1", call)).cached).toBe(false);
    const again = await cache.get("h1", call);
    expect(again.cached).toBe(true);
    expect(again.bytes[0]).toBe(1);
    expect(calls).toBe(1);
    await cache.get("h1", call, true);
    expect(calls).toBe(2);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

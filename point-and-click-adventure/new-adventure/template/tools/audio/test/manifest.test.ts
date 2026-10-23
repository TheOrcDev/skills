import { expect, test } from "bun:test";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { buildManifest, diff, entry } from "../src/manifest";

const line = (id: string, text: string) => entry({ id, speaker: "Hero", text, direction: "", line: 1 }, "x.dialogue");

test("diff sorts lines into new, changed, removed and unchanged", () => {
  const manifest = [line("A", "same"), line("B", "new words"), line("C", "brand new")];
  const lock = { A: { textHash: line("A", "same").textHash }, B: { textHash: line("B", "old words").textHash }, Z: { textHash: "gone" } };
  expect(diff(manifest, lock)).toEqual({ added: ["C"], changed: ["B"], removed: ["Z"], unchanged: ["A"] });
});

test("direction is part of what is spoken", () => {
  const plain = entry({ id: "A", speaker: "Hero", text: "Hello.", direction: "", line: 1 }, "x");
  const whispered = entry({ id: "A", speaker: "Hero", text: "Hello.", direction: "whispers", line: 1 }, "x");
  expect(plain.textHash).not.toBe(whispered.textHash);
});

test("the manifest gathers every file, sorted by id, and refuses a repeated id", () => {
  const dir = mkdtempSync(join(tmpdir(), "past-audio-"));
  try {
    mkdirSync(join(dir, "sub"));
    writeFileSync(join(dir, "b.dialogue"), "Hero: Second. [ID:B_1]\n");
    writeFileSync(join(dir, "sub", "a.dialogue"), "Hero: First. [ID:A_1]\n");
    expect(buildManifest(dir, dir, "Hero").map((e) => [e.id, e.file])).toEqual([["A_1", "sub/a.dialogue"], ["B_1", "b.dialogue"]]);
    writeFileSync(join(dir, "c.dialogue"), "Hero: Again. [ID:A_1]\n");
    expect(() => buildManifest(dir, dir, "Hero")).toThrow("A_1");
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

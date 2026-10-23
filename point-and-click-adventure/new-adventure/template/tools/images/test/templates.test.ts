import { expect, test } from "bun:test";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { parseRequest } from "../src/request";
import { fill, nextId, requestFile } from "../src/templates";

test("fill needs every placeholder", () => {
  expect(fill("a {x} b", { x: "1" })).toBe("a 1 b");
  expect(() => fill("{y}", {})).toThrow("{y}");
});

test("a written request parses, with Sol and the template's prompt", () => {
  const dir = mkdtempSync(join(tmpdir(), "past-templates-"));
  mkdirSync(join(dir, "prompts"));
  writeFileSync(join(dir, "prompts", "now.txt"), "A {place}.");
  writeFileSync(join(dir, "IMG-0041-old.md"), "");
  expect(nextId(dir)).toBe("IMG-0042");
  expect(nextId(dir, [42])).toBe("IMG-0043");
  const text = requestFile("IMG-0042", { slug: "s", title: "T", kind: "now", purpose: "P", requested: "plan 001", references: [], fields: { place: "crypt" } }, join(dir, "prompts"), "2026-10-11");
  const request = parseRequest(text, dir);
  expect(request).toMatchObject({ id: "IMG-0042", plan: "001", prompt: "A crypt." });
  expect(request.generation).toMatchObject({ model: "codex/gpt-6.1-sol", n: 3, background: "opaque" });
});

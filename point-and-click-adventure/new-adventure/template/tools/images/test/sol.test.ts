import { afterEach, beforeEach, describe, expect, test } from "bun:test";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { readLedger } from "../src/ledger";
import { parseRequest } from "../src/request";
import { runRequest } from "../src/run-request";
import { makeSolGenerate, orientation, parseEvents, pngSize, solInstructions, type CodexRunner } from "../src/sol";
import { requestText } from "./fixtures";

/** A PNG header claiming 1672x941. */
const PNG = new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0, 0, 0, 13, 0x49, 0x48, 0x44, 0x52, 0, 0, 0x06, 0x88, 0, 0, 0x03, 0xad, 8, 2]);

let root: string;
let calls: { args: string[]; stdin: string }[];

/** Pretends to be codex: writes `count` images under the thread's folder and prints its events. */
const fakeCodex = (count: number): CodexRunner => async (args, stdin) => {
  calls.push({ args, stdin });
  const dir = join(root, "generated", "thread-1");
  mkdirSync(dir, { recursive: true });
  for (let index = 0; index < count; index++) writeFileSync(join(dir, `exec-${index}.png`), PNG);
  const stdout = [
    JSON.stringify({ type: "thread.started", thread_id: "thread-1" }),
    JSON.stringify({ type: "item.completed", item: { type: "agent_message", text: "DONE" } }),
    JSON.stringify({ type: "turn.completed", usage: { input_tokens: 4000, output_tokens: 50 } }),
  ].join("\n");
  return { code: 0, stdout, stderr: "" };
};

beforeEach(() => {
  root = mkdtempSync(join(tmpdir(), "past-sol-"));
  calls = [];
});

afterEach(() => rmSync(root, { recursive: true, force: true }));

describe("sol helpers", () => {
  test("reads a PNG's size and the codex events", () => {
    expect(pngSize(PNG)).toEqual({ width: 1672, height: 941 });
    const events = parseEvents('{"type":"thread.started","thread_id":"t"}\nnoise\n{"type":"turn.completed","usage":{"input_tokens":3,"output_tokens":4}}');
    expect(events).toMatchObject({ threadId: "t", inputTokens: 3, outputTokens: 4 });
  });

  test("passes the prompt verbatim with the count, shape and mode", () => {
    const text = solInstructions("A grey crypt.", 3, 1, "2560x1440", "opaque");
    expect(text).toContain("exactly 3 times");
    expect(text).toContain("EDIT");
    expect(text.endsWith("PROMPT:\nA grey crypt.")).toBe(true);
    expect(orientation("1024x2048")).toContain("portrait");
  });
});

describe("runRequest through Sol", () => {
  test("copies Sol's images untouched and records them at no cost", async () => {
    const requestPath = join(root, "IMG-0007-nave.md");
    writeFileSync(join(root, "ref.png"), PNG);
    writeFileSync(requestPath, requestText({ generation: { model: "codex/gpt-6.1-sol", n: 2, references: ["ref.png"] } }));
    const request = parseRequest(readFileSync(requestPath, "utf8"), root);
    const generate = makeSolGenerate({ workDir: join(root, "work"), generatedRoot: join(root, "generated"), runner: fakeCodex(2) });

    const result = await runRequest(request, {
      root,
      rawDir: join(root, "raw"),
      ledgerPath: join(root, "raw", "ledger.json"),
      requestPath,
      generate,
      pricing: { inputUsdPerToken: 0, outputUsdPerToken: 0 },
      now: () => new Date("2026-10-11T12:00:00Z"),
    });

    expect(result).toMatchObject({ files: ["IMG-0007-v1.png", "IMG-0007-v2.png"], costUsd: 0, costSource: "plan" });
    expect(new Uint8Array(readFileSync(join(root, "raw", "IMG-0007", "IMG-0007-v1.png")))).toEqual(PNG);
    const args = calls[0].args;
    expect(args.slice(0, 5)).toEqual(["exec", "-m", "gpt-6.1-sol", "-s", "read-only"]);
    expect(args).toContain("-i");
    const receipt = JSON.parse(readFileSync(join(root, "raw", "IMG-0007", "receipt.json"), "utf8"));
    expect(receipt.rounds[0].providerMetadata.codex).toMatchObject({ threadId: "thread-1", pixelSizes: [{ width: 1672, height: 941 }, { width: 1672, height: 941 }] });
    expect(readLedger(join(root, "raw", "ledger.json"))[0]).toMatchObject({ costUsd: 0, costSource: "plan" });
    expect(readFileSync(requestPath, "utf8")).toContain("0 (ChatGPT plan)");
  });

  test("refuses a mask and reports a short count", async () => {
    const generate = makeSolGenerate({ workDir: join(root, "work"), generatedRoot: join(root, "generated"), runner: fakeCodex(1) });
    const call = (prompt: unknown, n: number) => (generate as unknown as (options: unknown) => Promise<{ warnings: unknown[] }>)({ model: "codex/gpt-6.1-sol", prompt, n, size: "2560x1440" });
    await expect(call({ text: "x", images: [PNG], mask: PNG }, 1)).rejects.toThrow("mask");
    const result = await call("A crypt.", 2);
    expect(result.warnings).toEqual([{ type: "count", message: "asked for 2 images, Sol made 1" }]);
  });
});

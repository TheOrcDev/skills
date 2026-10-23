import { afterEach, beforeEach, describe, expect, test } from "bun:test";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { readLedger } from "../src/ledger";
import { parseRequest } from "../src/request";
import { callCost, runRequest, type GenerateFn } from "../src/run-request";
import { requestText } from "./fixtures";

const PNG = new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 1, 2, 3]);

let root: string;
let calls: unknown[];

const fakeGenerate = ((options: unknown) => {
  calls.push(options);
  const { n } = options as { n: number };
  return Promise.resolve({
    images: Array.from({ length: n }, () => ({ base64: "", uint8Array: PNG, mediaType: "image/png" })),
    warnings: [],
    usage: { inputTokens: 100, outputTokens: 4000, totalTokens: 4100 },
    providerMetadata: { openai: { images: [] } },
  });
}) as unknown as GenerateFn;

const options = (requestPath: string) => ({
  root,
  rawDir: join(root, "raw"),
  ledgerPath: join(root, "raw", "ledger.json"),
  requestPath,
  generate: fakeGenerate,
  pricing: { inputUsdPerToken: 5e-6, outputUsdPerToken: 30e-6 },
  now: () => new Date("2026-10-10T12:00:00Z"),
});

beforeEach(() => {
  root = mkdtempSync(join(tmpdir(), "past-images-"));
  calls = [];
});

afterEach(() => rmSync(root, { recursive: true, force: true }));

describe("callCost", () => {
  const pricing = { inputUsdPerToken: 5e-6, outputUsdPerToken: 30e-6 };

  test("prefers the gateway's billed cost", () => {
    expect(callCost({ gateway: { cost: "0.055618" } }, 3578, 956, () => 9, pricing)).toEqual({ costUsd: 0.055618, costSource: "gateway" });
  });

  test("falls back to tokens, then to the estimate", () => {
    expect(callCost({}, 100, 4000, () => 9, pricing).costSource).toBe("tokens");
    expect(callCost(undefined, null, null, () => 9, pricing)).toEqual({ costUsd: 9, costSource: "estimate" });
  });
});

describe("runRequest", () => {
  test("text-to-image writes variants, receipt, ledger and the Delivery row", async () => {
    const requestPath = join(root, "IMG-0007-nave.md");
    writeFileSync(requestPath, requestText());
    const request = parseRequest(readFileSync(requestPath, "utf8"), root);

    const result = await runRequest(request, options(requestPath));

    expect(result.files).toEqual(["IMG-0007-v1.png", "IMG-0007-v2.png"]);
    expect(result.costUsd).toBeCloseTo(100 * 5e-6 + 4000 * 30e-6, 6);
    expect((calls[0] as { prompt: unknown }).prompt).toBe("A ruined stone harbour stair, monochrome, heavy fog.");
    expect((calls[0] as { providerOptions: unknown }).providerOptions).toEqual({ openai: { quality: "medium", background: "opaque" } });

    const receipt = JSON.parse(readFileSync(join(root, "raw", "IMG-0007", "receipt.json"), "utf8"));
    expect(receipt.rounds[0].files.map((f: { file: string }) => f.file)).toEqual(["IMG-0007-v1.png", "IMG-0007-v2.png"]);
    expect(receipt.rounds[0].prompt).toBe(request.prompt);

    expect(readLedger(join(root, "raw", "ledger.json"))[0]).toMatchObject({ id: "IMG-0007", plan: "002", round: 1, costSource: "tokens" });

    const updated = readFileSync(requestPath, "utf8");
    expect(updated).toContain("status: delivered");
    expect(updated).toContain("| 1 | 2026-10-10T12:00Z | IMG-0007-v1.png, IMG-0007-v2.png | openai/gpt-image-2.5-flare | 2560x1440 / medium | 0.121 |");
  });

  test("an edit sends the references and mask, and a second round continues the numbering", async () => {
    mkdirSync(join(root, "refs"));
    writeFileSync(join(root, "refs", "now.png"), PNG);
    writeFileSync(join(root, "refs", "mask.png"), PNG);
    const requestPath = join(root, "IMG-0007-nave.md");
    writeFileSync(requestPath, requestText({ generation: { model: "openai/gpt-image-2.5-sunburst", n: 1, references: ["refs/now.png"], mask: "refs/mask.png" } }));

    await runRequest(parseRequest(readFileSync(requestPath, "utf8"), root), options(requestPath));
    const prompt = (calls[0] as { prompt: { text: string; images: Uint8Array[]; mask: Uint8Array } }).prompt;
    expect(prompt.text).toBe("A ruined stone harbour stair, monochrome, heavy fog.");
    expect(prompt.images).toHaveLength(1);
    expect(prompt.mask).toEqual(PNG);

    writeFileSync(requestPath, readFileSync(requestPath, "utf8").replace("status: delivered", "status: revise"));
    const second = await runRequest(parseRequest(readFileSync(requestPath, "utf8"), root), options(requestPath));
    expect(second.round).toBe(2);
    expect(second.files).toEqual(["IMG-0007-v2.png"]);
    expect(readLedger(join(root, "raw", "ledger.json"))).toHaveLength(2);
  });
});

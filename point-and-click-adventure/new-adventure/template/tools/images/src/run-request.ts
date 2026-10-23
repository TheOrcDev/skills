// Runs one image request: calls the model, writes the raw variants, the receipt,
// the ledger entry and the request's Delivery row. Raw files are never overwritten.
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import type { generateImage } from "ai";
import { appendLedger, estimateCost, type LedgerEntry } from "./ledger";
import { withDeliveryRow, withStatus, type ImageRequest } from "./request";

export type GenerateFn = typeof generateImage;

export interface Pricing {
  inputUsdPerToken: number;
  outputUsdPerToken: number;
}

export interface RunOptions {
  root: string;
  rawDir: string;
  ledgerPath: string;
  requestPath: string;
  generate: GenerateFn;
  pricing: Pricing;
  now?: () => Date;
}

export interface RunResult {
  round: number;
  files: string[];
  costUsd: number;
  costSource: LedgerEntry["costSource"];
  warnings: unknown[];
}

interface ReceiptRound {
  round: number;
  date: string;
  model: string;
  size: string;
  quality: string;
  n: number;
  background: string;
  references: { path: string; sha256: string }[];
  mask: { path: string; sha256: string } | null;
  prompt: string;
  files: { file: string; sha256: string; mediaType: string }[];
  usage: { inputTokens: number | null; outputTokens: number | null };
  costUsd: number;
  costSource: LedgerEntry["costSource"];
  warnings: unknown[];
  providerMetadata: unknown;
}

const sha256 = (data: Uint8Array) => createHash("sha256").update(data).digest("hex");

const extensionFor = (mediaType: string) => ({ "image/png": "png", "image/jpeg": "jpg", "image/webp": "webp" })[mediaType] ?? "png";

/** The next variant number after the files already in the request's raw folder. */
function nextVariant(dir: string, id: string): number {
  if (!existsSync(dir)) return 1;
  const numbers = readdirSync(dir)
    .map((file) => new RegExp(`^${id}-v(\\d+)\\.`).exec(file))
    .filter((match): match is RegExpExecArray => match !== null)
    .map((match) => Number(match[1]));
  return numbers.length ? Math.max(...numbers) + 1 : 1;
}

/** The billed cost: the gateway's own figure when it reports one, else tokens × price, else an estimate. */
export function callCost(
  providerMetadata: unknown,
  inputTokens: number | null,
  outputTokens: number | null,
  estimate: () => number,
  pricing: Pricing,
): { costUsd: number; costSource: LedgerEntry["costSource"] } {
  if ((providerMetadata as { codex?: unknown } | undefined)?.codex) return { costUsd: 0, costSource: "plan" };
  const gatewayCost = Number((providerMetadata as { gateway?: { cost?: string } } | undefined)?.gateway?.cost);
  if (Number.isFinite(gatewayCost) && gatewayCost > 0) return { costUsd: gatewayCost, costSource: "gateway" };
  if (inputTokens !== null && outputTokens !== null) {
    return { costUsd: inputTokens * pricing.inputUsdPerToken + outputTokens * pricing.outputUsdPerToken, costSource: "tokens" };
  }
  return { costUsd: estimate(), costSource: "estimate" };
}

export async function runRequest(request: ImageRequest, options: RunOptions): Promise<RunResult> {
  const { generation } = request;
  const now = (options.now ?? (() => new Date()))();
  const dir = resolve(options.rawDir, request.id);
  mkdirSync(dir, { recursive: true });

  const receiptPath = join(dir, "receipt.json");
  const receipt: { id: string; title: string; rounds: ReceiptRound[] } = existsSync(receiptPath)
    ? JSON.parse(readFileSync(receiptPath, "utf8"))
    : { id: request.id, title: request.title, rounds: [] };
  const round = receipt.rounds.length + 1;

  const references = generation.references.map((path) => ({ path, data: new Uint8Array(readFileSync(resolve(options.root, path))) }));
  const mask = generation.mask ? { path: generation.mask, data: new Uint8Array(readFileSync(resolve(options.root, generation.mask))) } : null;

  const result = await options.generate({
    model: generation.model,
    prompt: references.length
      ? { text: request.prompt, images: references.map((reference) => reference.data), ...(mask ? { mask: mask.data } : {}) }
      : request.prompt,
    n: generation.n,
    size: generation.size as `${number}x${number}`,
    providerOptions: { openai: { quality: generation.quality, background: generation.background } },
  });

  let variant = nextVariant(dir, request.id);
  const files: ReceiptRound["files"] = [];
  for (const image of result.images) {
    const file = `${request.id}-v${variant++}.${extensionFor(image.mediaType)}`;
    const path = join(dir, file);
    if (existsSync(path)) throw new Error(`refusing to overwrite ${path}`);
    writeFileSync(path, image.uint8Array);
    files.push({ file, sha256: sha256(image.uint8Array), mediaType: image.mediaType });
  }

  const inputTokens = result.usage?.inputTokens ?? null;
  const outputTokens = result.usage?.outputTokens ?? null;
  const { costUsd, costSource } = callCost(result.providerMetadata, inputTokens, outputTokens, () =>
    estimateCost(generation, options.pricing.outputUsdPerToken, options.pricing.inputUsdPerToken),
  options.pricing);

  receipt.rounds.push({
    round,
    date: now.toISOString(),
    model: generation.model,
    size: generation.size,
    quality: generation.quality,
    n: generation.n,
    background: generation.background,
    references: references.map((reference) => ({ path: reference.path, sha256: sha256(reference.data) })),
    mask: mask ? { path: mask.path, sha256: sha256(mask.data) } : null,
    prompt: request.prompt,
    files,
    usage: { inputTokens, outputTokens },
    costUsd,
    costSource,
    warnings: result.warnings ?? [],
    providerMetadata: result.providerMetadata ?? null,
  });
  writeFileSync(receiptPath, JSON.stringify(receipt, null, 2) + "\n");

  appendLedger(options.ledgerPath, {
    id: request.id,
    round,
    plan: request.plan,
    model: generation.model,
    size: generation.size,
    quality: generation.quality,
    n: generation.n,
    date: now.toISOString(),
    files: files.map((entry) => entry.file),
    inputTokens,
    outputTokens,
    costUsd,
    costSource,
  });

  let text = readFileSync(options.requestPath, "utf8");
  text = withDeliveryRow(text, [
    String(round),
    now.toISOString().slice(0, 16) + "Z",
    files.map((entry) => entry.file).join(", "),
    generation.model,
    `${generation.size} / ${generation.quality}`,
    costSource === "plan" ? "0 (ChatGPT plan)" : `${costUsd.toFixed(3)}${costSource === "estimate" ? " (est.)" : ""}`,
  ]);
  writeFileSync(options.requestPath, withStatus(text, "delivered"));

  return { round, files: files.map((entry) => entry.file), costUsd, costSource, warnings: result.warnings ?? [] };
}

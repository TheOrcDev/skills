// GPT-6.1 Sol as an image engine (docs/decisions.md #44): a request whose model is
// `codex/gpt-6.1-sol` runs through the Codex CLI and its built-in image tool,
// billed to the operator's ChatGPT plan. Sol runs in a read-only sandbox and
// writes nothing; Codex keeps each image it generates under
// ~/.codex/generated_images/<thread id>/, and this module reads them from there
// untouched. It has the shape of the AI SDK's generateImage, so runRequest
// writes the raws, receipt, ledger and Delivery row exactly as for the gateway.
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import type { GenerateFn } from "./run-request";

export const SOL_PREFIX = "codex/";

export const isSolModel = (model: string) => model.startsWith(SOL_PREFIX);

export interface CodexResult {
  code: number;
  stdout: string;
  stderr: string;
}

/** Runs `codex` with arguments and stdin. Replaced in tests. */
export type CodexRunner = (args: string[], stdin: string) => Promise<CodexResult>;

export const runCodex: CodexRunner = (args, stdin) =>
  new Promise((resolve, reject) => {
    const child = spawn("codex", args, { stdio: ["pipe", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => (stdout += chunk));
    child.stderr.on("data", (chunk) => (stderr += chunk));
    child.on("error", reject);
    child.on("close", (code) => resolve({ code: code ?? 1, stdout, stderr }));
    child.stdin.end(stdin);
  });

export interface SolOptions {
  /** Scratch folder for reference copies; Codex's working root. */
  workDir: string;
  /** Where Codex keeps generated images. */
  generatedRoot?: string;
  runner?: CodexRunner;
}

/** Width and height from a PNG's IHDR chunk. */
export function pngSize(data: Uint8Array): { width: number; height: number } | null {
  const signature = [0x89, 0x50, 0x4e, 0x47];
  if (data.length < 24 || !signature.every((byte, index) => data[index] === byte)) return null;
  const view = new DataView(data.buffer, data.byteOffset, data.byteLength);
  return { width: view.getUint32(16), height: view.getUint32(20) };
}

/** The shape asked of the image tool, from the request's size. */
export function orientation(size: string): string {
  const [width, height] = size.split("x").map(Number);
  if (width > height * 1.2) return "landscape (wide), as wide as the tool allows";
  if (height > width * 1.2) return "portrait (tall)";
  return "square";
}

/** The instructions Sol receives. The request's prompt goes to the image tool verbatim. */
export function solInstructions(prompt: string, n: number, references: number, size: string, background: string): string {
  const mode = references
    ? `Each call gives the attached image${references > 1 ? "s" : ""} to the tool as input (an EDIT call). The PROMPT says whether to edit the first one in place or to paint a new scene in its style.`
    : "Each call is a new image (no input image).";
  return [
    "You are the image engine for a point-and-click adventure game. Follow this exactly:",
    `- Call your image generation tool exactly ${n} time${n > 1 ? "s" : ""}, one image per call. ${mode}`,
    "- Pass the PROMPT below to the tool verbatim, every time. Do not shorten, embellish or translate it.",
    `- Image shape: ${orientation(size)}.`,
    `- Background: ${background === "transparent" ? "transparent" : "opaque"}.`,
    "- Do not run shell commands, do not read or write files, and do not edit anything.",
    "- When all images are generated, reply with one line: DONE.",
    "",
    "PROMPT:",
    prompt,
  ].join("\n");
}

interface CodexEvents {
  threadId: string | null;
  messages: string[];
  inputTokens: number | null;
  outputTokens: number | null;
}

export function parseEvents(stdout: string): CodexEvents {
  const events: CodexEvents = { threadId: null, messages: [], inputTokens: null, outputTokens: null };
  for (const line of stdout.split("\n")) {
    if (!line.startsWith("{")) continue;
    let event: { type?: string; thread_id?: string; item?: { type?: string; text?: string }; usage?: { input_tokens?: number; output_tokens?: number } };
    try {
      event = JSON.parse(line);
    } catch {
      continue;
    }
    if (event.type === "thread.started" && event.thread_id) events.threadId = event.thread_id;
    if (event.type === "item.completed" && event.item?.type === "agent_message" && event.item.text) events.messages.push(event.item.text.trim());
    if (event.type === "turn.completed" && event.usage) {
      events.inputTokens = event.usage.input_tokens ?? null;
      events.outputTokens = event.usage.output_tokens ?? null;
    }
  }
  return events;
}

/** A generateImage-shaped function that asks Sol for the images. */
export function makeSolGenerate(options: SolOptions): GenerateFn {
  const runner = options.runner ?? runCodex;
  const generatedRoot = options.generatedRoot ?? join(homedir(), ".codex", "generated_images");

  const generate = async (call: {
    model: string;
    prompt: string | { text: string; images: Uint8Array[]; mask?: Uint8Array };
    n: number;
    size: string;
    providerOptions?: { openai?: { background?: string } };
  }) => {
    if (typeof call.prompt !== "string" && call.prompt.mask) throw new Error("Sol can't take a mask; run this request through the gateway");
    const text = typeof call.prompt === "string" ? call.prompt : call.prompt.text;
    const references = typeof call.prompt === "string" ? [] : call.prompt.images;
    const model = call.model.slice(SOL_PREFIX.length);

    mkdirSync(options.workDir, { recursive: true });
    const attachments = references.map((data, index) => {
      const path = join(options.workDir, `reference-${index + 1}.png`);
      writeFileSync(path, data);
      return path;
    });

    const args = ["exec", "-m", model, "-s", "read-only", "--skip-git-repo-check", "--ephemeral", "-C", options.workDir, "--json"];
    for (const path of attachments) args.push("-i", path);
    args.push("-");
    const background = call.providerOptions?.openai?.background ?? "opaque";
    const result = await runner(args, solInstructions(text, call.n, references.length, call.size, background));
    writeFileSync(join(options.workDir, "codex-events.jsonl"), result.stdout);
    const events = parseEvents(result.stdout);
    if (result.code !== 0 || !events.threadId) {
      throw new Error(`codex exec failed (exit ${result.code}): ${result.stderr.trim().split("\n").slice(-3).join(" / ")}`);
    }

    const dir = join(generatedRoot, events.threadId);
    const files = existsSync(dir)
      ? readdirSync(dir)
          .filter((file) => file.endsWith(".png"))
          .map((file) => join(dir, file))
          .sort((a, b) => statSync(a).mtimeMs - statSync(b).mtimeMs)
      : [];
    if (files.length === 0) throw new Error(`Sol generated no images (thread ${events.threadId}): ${events.messages.join(" / ")}`);

    const warnings: unknown[] = [];
    if (files.length !== call.n) warnings.push({ type: "count", message: `asked for ${call.n} images, Sol made ${files.length}` });
    const images = files.map((path) => ({ base64: "", uint8Array: new Uint8Array(readFileSync(path)), mediaType: "image/png" }));
    return {
      images,
      warnings,
      usage: { inputTokens: events.inputTokens ?? undefined, outputTokens: events.outputTokens ?? undefined },
      providerMetadata: {
        codex: {
          model,
          threadId: events.threadId,
          sources: files,
          pixelSizes: images.map((image) => pngSize(image.uint8Array)),
          messages: events.messages,
        },
      },
    };
  };
  return generate as unknown as GenerateFn;
}

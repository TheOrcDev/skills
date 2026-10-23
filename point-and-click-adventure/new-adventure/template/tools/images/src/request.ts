// Parses and validates image request files (art-source/requests/IMG-####-*.md).
// The format is documented in art-source/requests/_TEMPLATE.md.
import { existsSync } from "node:fs";
import { resolve } from "node:path";

export const QUALITIES = ["low", "medium", "high", "xhigh", "max", "auto"] as const;
export type Quality = (typeof QUALITIES)[number];
export const BACKGROUNDS = ["opaque", "transparent", "auto"] as const;
export type Background = (typeof BACKGROUNDS)[number];

export interface Generation {
  model: string;
  size: string;
  quality: Quality;
  n: number;
  background: Background;
  references: string[];
  mask: string | null;
}

export interface ImageRequest {
  id: string;
  title: string;
  status: string;
  plan: string;
  operatorApproval: string;
  generation: Generation;
  prompt: string;
}

export class RequestError extends Error {}

/** Width and height in pixels, from "WIDTHxHEIGHT". */
export function parseSize(size: string): { width: number; height: number } {
  const match = /^(\d+)x(\d+)$/.exec(size);
  if (!match) throw new RequestError(`size must look like 2560x1440, got "${size}"`);
  return { width: Number(match[1]), height: Number(match[2]) };
}

/** GPT Image 2.5 size rules: multiples of 16, aspect 1:3–3:1, edges ≤ 3840, 655,360–8,294,400 pixels. */
export function validateSize(size: string): void {
  const { width, height } = parseSize(size);
  if (width % 16 !== 0 || height % 16 !== 0) throw new RequestError(`size ${size}: both sides must be multiples of 16`);
  const ratio = width / height;
  if (ratio < 1 / 3 || ratio > 3) throw new RequestError(`size ${size}: aspect must be between 1:3 and 3:1`);
  if (width > 3840 || height > 3840) throw new RequestError(`size ${size}: no edge may exceed 3840`);
  const pixels = width * height;
  if (pixels < 655_360 || pixels > 8_294_400) throw new RequestError(`size ${size}: pixel count must be 655,360–8,294,400`);
}

function section(text: string, heading: string): string {
  const start = text.search(new RegExp(`^## ${heading}\\s*$`, "m"));
  if (start < 0) throw new RequestError(`missing "## ${heading}" section`);
  const rest = text.slice(start).split("\n").slice(1).join("\n");
  const next = rest.search(/^## /m);
  return next < 0 ? rest : rest.slice(0, next);
}

function fenced(block: string, language: string, heading: string): string {
  const match = new RegExp("```" + language + "\\n([\\s\\S]*?)\\n```").exec(block);
  if (!match) throw new RequestError(`"## ${heading}" needs a \`\`\`${language} block`);
  return match[1];
}

function field(text: string, name: string): string {
  const match = new RegExp(`^${name}:\\s*(\\S+)`, "m").exec(text);
  if (!match) throw new RequestError(`missing "${name}:" line`);
  return match[1];
}

/** Parses a request file. `root` resolves reference and mask paths for validation. */
export function parseRequest(text: string, root: string): ImageRequest {
  const heading = /^# (IMG-\d{4}) — (.+)$/m.exec(text);
  if (!heading) throw new RequestError('the first heading must be "# IMG-#### — title"');

  let raw: Record<string, unknown>;
  try {
    raw = JSON.parse(fenced(section(text, "Generation"), "json", "Generation"));
  } catch (error) {
    if (error instanceof RequestError) throw error;
    throw new RequestError(`Generation block is not valid JSON: ${(error as Error).message}`);
  }

  const generation: Generation = {
    model: String(raw.model ?? ""),
    size: String(raw.size ?? ""),
    quality: String(raw.quality ?? "medium") as Quality,
    n: Number(raw.n ?? 1),
    background: String(raw.background ?? "opaque") as Background,
    references: Array.isArray(raw.references) ? raw.references.map(String) : [],
    mask: raw.mask == null ? null : String(raw.mask),
  };

  if (!/^[a-z0-9-]+\/[\w.-]+$/.test(generation.model)) throw new RequestError(`model must be a gateway id like openai/gpt-image-2.5-flare, got "${generation.model}"`);
  validateSize(generation.size);
  if (!QUALITIES.includes(generation.quality)) throw new RequestError(`quality must be one of ${QUALITIES.join(", ")}`);
  if (!Number.isInteger(generation.n) || generation.n < 1 || generation.n > 10) throw new RequestError("n must be an integer from 1 to 10");
  if (!BACKGROUNDS.includes(generation.background)) throw new RequestError(`background must be one of ${BACKGROUNDS.join(", ")}`);
  if (generation.mask && generation.references.length === 0) throw new RequestError("a mask needs at least one reference image");
  for (const path of [...generation.references, ...(generation.mask ? [generation.mask] : [])]) {
    if (!existsSync(resolve(root, path))) throw new RequestError(`file not found: ${path}`);
  }

  const prompt = fenced(section(text, "Prompt"), "text", "Prompt").trim();
  if (!prompt || prompt === "…") throw new RequestError("the Prompt block is empty");

  return {
    id: heading[1],
    title: heading[2].trim(),
    status: field(text, "status"),
    plan: field(text, "plan"),
    operatorApproval: field(text, "operator-approval"),
    generation,
    prompt,
  };
}

/** Sets the `status:` line. */
export function withStatus(text: string, status: string): string {
  return text.replace(/^status:\s*\S+/m, `status: ${status}`);
}

/** Appends a row to the Delivery table (the table directly under "## Delivery"). */
export function withDeliveryRow(text: string, cells: string[]): string {
  const start = text.search(/^## Delivery\s*$/m);
  if (start < 0) throw new RequestError('missing "## Delivery" section');
  const after = text.slice(start);
  const next = after.slice(1).search(/^## /m);
  const sectionText = next < 0 ? after : after.slice(0, next + 1);
  const lines = sectionText.split("\n");
  let lastRow = -1;
  lines.forEach((line, index) => {
    if (line.startsWith("|")) lastRow = index;
  });
  if (lastRow < 0) throw new RequestError("the Delivery section has no table");
  lines.splice(lastRow + 1, 0, `| ${cells.join(" | ")} |`);
  return text.slice(0, start) + lines.join("\n") + text.slice(start + sectionText.length);
}

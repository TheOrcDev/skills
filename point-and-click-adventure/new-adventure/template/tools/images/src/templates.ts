// Writes request files from short specs and the shared prompt templates in
// art-source/style/prompts/, so every request of a kind keeps one
// style. Each template's {field} placeholders come from the spec's `fields`.
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

export interface RequestSpec {
  slug: string;
  title: string;
  /** A template in art-source/style/prompts/ (now, then, closeup, npc, items), or "raw" with `prompt`. */
  kind: string;
  purpose: string;
  requested: string;
  references: string[];
  n?: number;
  model?: string;
  size?: string;
  background?: "opaque" | "transparent";
  fields?: Record<string, string>;
  prompt?: string;
  must?: string[];
  mustNot?: string[];
  criteria?: string[];
  plan?: string;
}

export const SOL_MODEL = "codex/gpt-6.1-sol";

/** Fills a template's {field}s; every placeholder must be given. */
export function fill(template: string, fields: Record<string, string>): string {
  return template.replace(/\{(\w+)\}/g, (_, name: string) => {
    if (!(name in fields)) throw new Error(`template field {${name}} is missing`);
    return fields[name];
  });
}

/** The next free IMG number after those in the requests folder. */
export function nextId(requestsDir: string, taken: number[] = []): string {
  const numbers = readdirSync(requestsDir)
    .map((file) => /^IMG-(\d{4})-/.exec(file))
    .filter((match): match is RegExpExecArray => match !== null)
    .map((match) => Number(match[1]))
    .concat(taken);
  return `IMG-${String((numbers.length ? Math.max(...numbers) : 0) + 1).padStart(4, "0")}`;
}

const list = (items: string[] | undefined, fallback: string) => (items?.length ? items : [fallback]).map((item) => `- ${item}`).join("\n");

export function requestFile(id: string, spec: RequestSpec, promptsDir: string, date: string): string {
  const prompt = spec.kind === "raw" ? (spec.prompt ?? "") : fill(readFileSync(join(promptsDir, `${spec.kind}.txt`), "utf8").trim(), spec.fields ?? {});
  const generation = {
    model: spec.model ?? SOL_MODEL,
    size: spec.size ?? "2560x1440",
    quality: "high",
    n: spec.n ?? (spec.kind === "then" ? 2 : 3),
    background: spec.background ?? (spec.kind === "npc" || spec.kind === "items" ? "transparent" : "opaque"),
    references: spec.references,
    mask: null,
  };
  return `# ${id} — ${spec.title}

status: open
operator-approval: not-required
plan: ${spec.plan ?? "001"}
requested: ${date} by Claude for ${spec.requested}

\`status\` is one of open, delivered, revise, accepted, rejected or cancelled.
\`operator-approval\` is required or not-required. \`plan\` names the plan whose
image budget pays for this request.

## Purpose

${spec.purpose}

## Generation

\`tools/images/run.ts\` reads this block.

\`\`\`json
${JSON.stringify(generation, null, 2)}
\`\`\`

## Prompt

The tool sends this text block verbatim.

\`\`\`text
${prompt}
\`\`\`

## Must have

${list(spec.must, "What the purpose describes, in the game's style.")}

## Must not have

${list(spec.mustNot, "Figures, readable text, or a frame.")}

## Acceptance criteria

Claude checks these.

${(spec.criteria?.length ? spec.criteria : ["It does what the purpose asks, in the style of its references."]).map((item) => `- [ ] ${item}`).join("\n")}

## Delivery

Written by \`tools/images\`. Files go to \`art-source/raw/<ID>/\`, unmodified, with
\`receipt.json\` next to them.

| Round | Date (UTC) | Files | Model | Size / quality | Cost (USD) |
|---|---|---|---|---|---|

## Review

Filled in by Claude and the operator.

| Round | Date (UTC) | Verdict | Notes |
|---|---|---|---|
`;
}

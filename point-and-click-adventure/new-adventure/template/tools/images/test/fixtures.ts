/** A request file in the template's format. */
export function requestText(overrides: { generation?: Record<string, unknown>; prompt?: string; status?: string } = {}): string {
  const generation = {
    model: "openai/gpt-image-2.5-flare",
    size: "2560x1440",
    quality: "medium",
    n: 2,
    background: "opaque",
    references: [],
    mask: null,
    ...overrides.generation,
  };
  return `# IMG-0007 — Harbour steps, now

status: ${overrides.status ?? "open"}
operator-approval: required
plan: 002
requested: 2026-10-10 by Claude for plan 002, slice 1

## Purpose

Test request.

## Generation

\`\`\`json
${JSON.stringify(generation, null, 2)}
\`\`\`

## Prompt

\`\`\`text
${overrides.prompt ?? "A ruined stone harbour stair, monochrome, heavy fog."}
\`\`\`

## Must have

- fog

## Delivery

| Round | Date (UTC) | Files | Model | Size / quality | Cost (USD) |
|---|---|---|---|---|---|

## Review

| Round | Date (UTC) | Verdict | Notes |
|---|---|---|---|
`;
}

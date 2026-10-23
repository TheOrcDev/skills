import { createHash } from "node:crypto";

/** JSON with sorted keys, so equal values hash the same. */
export function canonical(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>)
      .filter(([, v]) => v !== undefined)
      .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0));
    return `{${entries.map(([k, v]) => `${JSON.stringify(k)}:${canonical(v)}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

export function sha256(text: string): string {
  return createHash("sha256").update(text).digest("hex");
}

/** The cache key of one API request (audio-pipeline.md §3): the same request
 * never calls the API twice. */
export function requestHash(request: { endpoint: string; model?: string; voice?: string; settings?: unknown; text?: string }): string {
  return sha256(canonical(request));
}

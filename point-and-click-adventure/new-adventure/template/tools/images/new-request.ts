// Writes request files from a JSON spec (or an array of specs) and prints their IDs.
// Usage, from the repository root: bun tools/images/new-request.ts specs.json
// The spec format is RequestSpec in src/templates.ts.
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { repoRoot, requestsDir } from "./src/paths";
import { parseRequest } from "./src/request";
import { nextId, requestFile, type RequestSpec } from "./src/templates";

const path = process.argv[2];
if (!path) {
  console.error("usage: bun tools/images/new-request.ts specs.json");
  process.exit(2);
}
const parsed = JSON.parse(readFileSync(resolve(path), "utf8"));
const specs: RequestSpec[] = Array.isArray(parsed) ? parsed : [parsed];
const date = new Date().toISOString().slice(0, 10);
const taken: number[] = [];
for (const spec of specs) {
  const id = nextId(requestsDir, taken);
  taken.push(Number(id.slice(4)));
  const file = join(requestsDir, `${id}-${spec.slug}.md`);
  if (existsSync(file)) throw new Error(`${file} exists`);
  const text = requestFile(id, spec, join(repoRoot, "art-source/style/prompts"), date);
  parseRequest(text, repoRoot);
  writeFileSync(file, text);
  console.log(`${id} ${spec.slug}`);
}

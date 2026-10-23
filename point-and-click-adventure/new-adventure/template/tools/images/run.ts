// Runs an image request through the Vercel AI Gateway (docs/decisions.md #25).
// A request whose model is codex/gpt-6.1-sol runs through Sol instead (#44).
// Usage, from the repository root: bun tools/images/run.ts IMG-0001 [--dry-run]
import { readdirSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { generateImage } from "ai";
import { credentialUsable, currentCredential, describeCredential } from "./src/credentials";
import { checkBudget, estimateCost, readBudgets, readLedger } from "./src/ledger";
import { budgetsPath, ledgerPath, rawDir, repoRoot, requestsDir } from "./src/paths";
import { isSolModel, makeSolGenerate } from "./src/sol";
import { fetchPricing } from "./src/pricing";
import { parseRequest, RequestError } from "./src/request";
import { runRequest } from "./src/run-request";

const [id, flag] = process.argv.slice(2);
if (!id || !/^IMG-\d{4}$/.test(id)) {
  console.error("usage: bun tools/images/run.ts IMG-0001 [--dry-run]");
  process.exit(2);
}

const file = readdirSync(requestsDir).find((name) => name.startsWith(`${id}-`) && name.endsWith(".md"));
if (!file) {
  console.error(`no request file art-source/requests/${id}-*.md`);
  process.exit(2);
}
const requestPath = join(requestsDir, file);

try {
  const request = parseRequest(readFileSync(requestPath, "utf8"), repoRoot);
  if (request.status !== "open" && request.status !== "revise") {
    throw new RequestError(`${id} is "${request.status}"; set "status: revise" to run another round`);
  }
  const sol = isSolModel(request.generation.model);
  const pricing = sol ? { source: "plan", inputUsdPerToken: 0, outputUsdPerToken: 0 } : await fetchPricing(request.generation.model);
  const estimate = estimateCost(request.generation, pricing.outputUsdPerToken, pricing.inputUsdPerToken);
  const budget = checkBudget(request.plan, readBudgets(budgetsPath), readLedger(ledgerPath), estimate);
  console.log(`${id} "${request.title}": ${request.generation.n}× ${request.generation.model} ${request.generation.size} ${request.generation.quality}${request.generation.references.length ? `, edit of ${request.generation.references.join(", ")}` : ""}`);
  console.log(`pricing (${pricing.source}): $${(pricing.inputUsdPerToken * 1e6).toFixed(2)}/M in, $${(pricing.outputUsdPerToken * 1e6).toFixed(2)}/M out`);
  console.log(budget.message);
  if (!budget.ok) process.exit(3);
  if (flag === "--dry-run") process.exit(0);
  if (!sol) {
    const credential = currentCredential();
    if (!credentialUsable(credential)) {
      console.error(describeCredential(credential));
      process.exit(4);
    }
  }

  // Outside the project: Godot would import anything under it, into the pack.
  const workDir = join(tmpdir(), "adventure-sol", `${id}-${Date.now()}`);
  const generate = sol ? makeSolGenerate({ workDir }) : generateImage;
  const result = await runRequest(request, { root: repoRoot, rawDir, ledgerPath, requestPath, generate, pricing });
  console.log(`round ${result.round}: ${result.files.join(", ")} — $${result.costUsd.toFixed(3)} (${result.costSource})`);
  for (const warning of result.warnings) console.warn("warning:", JSON.stringify(warning));
} catch (error) {
  if (error instanceof RequestError) {
    console.error(`${file}: ${error.message}`);
    process.exit(2);
  }
  throw error;
}

// The spend ledger (art-source/raw/ledger.json) and the per-plan budget guard.
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { parseSize, type Generation } from "./request";

export interface LedgerEntry {
  id: string;
  round: number;
  plan: string;
  model: string;
  size: string;
  quality: string;
  n: number;
  date: string;
  files: string[];
  inputTokens: number | null;
  outputTokens: number | null;
  costUsd: number;
  /** "plan": made by Sol on the operator's ChatGPT plan, so no dollars. */
  costSource: "gateway" | "tokens" | "estimate" | "plan";
}

/** Generation stops once a plan has spent this share of its budget. */
export const STOP_FRACTION = 0.8;

export function readLedger(path: string): LedgerEntry[] {
  return existsSync(path) ? (JSON.parse(readFileSync(path, "utf8")) as LedgerEntry[]) : [];
}

export function appendLedger(path: string, entry: LedgerEntry): void {
  const entries = readLedger(path);
  entries.push(entry);
  writeFileSync(path, JSON.stringify(entries, null, 2) + "\n");
}

export function spentFor(entries: LedgerEntry[], plan: string): number {
  return entries.filter((entry) => entry.plan === plan).reduce((sum, entry) => sum + entry.costUsd, 0);
}

export function readBudgets(path: string): Record<string, number> {
  return existsSync(path) ? (JSON.parse(readFileSync(path, "utf8")) as Record<string, number>) : {};
}

/** Output tokens per megapixel at each quality, from GPT Image's published token counts, rounded up. */
const OUTPUT_TOKENS_PER_MEGAPIXEL: Record<string, number> = {
  low: 300,
  medium: 1100,
  high: 4300,
  xhigh: 6500,
  max: 8700,
  auto: 4300,
};

/** A deliberately high estimate of a request's cost, used before generating. */
export function estimateCost(generation: Generation, outputUsdPerToken: number, inputUsdPerToken: number): number {
  const { width, height } = parseSize(generation.size);
  const megapixels = (width * height) / 1_048_576;
  const output = OUTPUT_TOKENS_PER_MEGAPIXEL[generation.quality] * megapixels * generation.n;
  const input = 2_000 + generation.references.length * 6_000 * megapixels;
  return output * outputUsdPerToken + input * inputUsdPerToken;
}

export interface BudgetCheck {
  ok: boolean;
  spent: number;
  budget: number;
  limit: number;
  message: string;
}

/** Refuses when the plan has no budget, or when spending `estimate` would pass 80% of it.
 * A plan with no budget may still run requests that cost nothing (Sol, on the
 * operator's ChatGPT plan), as long as it has spent nothing. */
export function checkBudget(plan: string, budgets: Record<string, number>, entries: LedgerEntry[], estimate: number): BudgetCheck {
  const budget = budgets[plan] ?? 0;
  const spent = spentFor(entries, plan);
  const limit = budget * STOP_FRACTION;
  if (budget <= 0 && estimate === 0 && spent === 0) {
    return { ok: true, spent, budget, limit, message: `plan ${plan}: no image budget; this request costs nothing (ChatGPT plan)` };
  }
  if (budget <= 0) {
    return { ok: false, spent, budget, limit, message: `plan ${plan} has no image budget in tools/images/budgets.json` };
  }
  if (spent + estimate > limit) {
    return {
      ok: false,
      spent,
      budget,
      limit,
      message: `plan ${plan}: $${spent.toFixed(2)} spent + ~$${estimate.toFixed(2)} for this request would pass 80% of the $${budget} budget. Stop and report to the operator.`,
    };
  }
  return { ok: true, spent, budget, limit, message: `plan ${plan}: $${spent.toFixed(2)} of $${budget} spent; this request ~$${estimate.toFixed(2)}` };
}

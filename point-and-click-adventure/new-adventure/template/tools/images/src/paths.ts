import { resolve } from "node:path";

/** Repository root, from tools/images/src. */
export const repoRoot = resolve(import.meta.dir, "..", "..", "..");
export const requestsDir = resolve(repoRoot, "art-source/requests");
export const rawDir = resolve(repoRoot, "art-source/raw");
export const ledgerPath = resolve(rawDir, "ledger.json");
export const budgetsPath = resolve(import.meta.dir, "..", "budgets.json");

// Prints image spend per plan against its budget.
// Usage, from the repository root: bun tools/images/budget.ts
import { readBudgets, readLedger, spentFor, STOP_FRACTION } from "./src/ledger";
import { budgetsPath, ledgerPath } from "./src/paths";

const budgets = readBudgets(budgetsPath);
const entries = readLedger(ledgerPath);
const plans = [...new Set([...Object.keys(budgets), ...entries.map((entry) => entry.plan)])].sort();
for (const plan of plans) {
  const spent = spentFor(entries, plan);
  const budget = budgets[plan] ?? 0;
  const calls = entries.filter((entry) => entry.plan === plan);
  const images = calls.reduce((sum, entry) => sum + entry.files.length, 0);
  console.log(`plan ${plan}: $${spent.toFixed(2)} of $${budget} (stop at $${(budget * STOP_FRACTION).toFixed(2)}), ${calls.length} calls, ${images} images`);
}

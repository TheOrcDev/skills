import { describe, expect, test } from "bun:test";
import { checkBudget, estimateCost, spentFor, type LedgerEntry } from "../src/ledger";
import type { Generation } from "../src/request";

const entry = (plan: string, costUsd: number): LedgerEntry => ({
  id: "IMG-0001",
  round: 1,
  plan,
  model: "openai/gpt-image-2.5-flare",
  size: "2560x1440",
  quality: "medium",
  n: 1,
  date: "2026-10-10T00:00:00.000Z",
  files: ["IMG-0001-v1.png"],
  inputTokens: 1,
  outputTokens: 1,
  costUsd,
  costSource: "tokens",
});

const generation = (quality: Generation["quality"], size = "2560x1440", n = 1): Generation => ({
  model: "openai/gpt-image-2.5-flare",
  size,
  quality,
  n,
  background: "opaque",
  references: [],
  mask: null,
});

describe("budget guard", () => {
  test("sums spend per plan", () => {
    expect(spentFor([entry("002", 1.5), entry("002", 2), entry("003", 9)], "002")).toBe(3.5);
  });

  test("allows spending up to 80% of the budget", () => {
    expect(checkBudget("002", { "002": 50 }, [entry("002", 30)], 9.99).ok).toBe(true);
  });

  test("refuses a request that would pass 80% of the budget", () => {
    const check = checkBudget("002", { "002": 50 }, [entry("002", 35)], 6);
    expect(check.ok).toBe(false);
    expect(check.message).toContain("Stop and report");
  });

  test("refuses a plan without a budget", () => {
    expect(checkBudget("009", { "002": 50 }, [], 0.01).ok).toBe(false);
  });

  test("lets a plan without a budget run requests that cost nothing (Sol)", () => {
    expect(checkBudget("010", { "002": 50 }, [], 0).ok).toBe(true);
    expect(checkBudget("010", { "002": 50 }, [entry("010", 0.5)], 0).ok).toBe(false);
  });
});

describe("estimateCost", () => {
  const price = (g: Generation) => estimateCost(g, 30e-6, 5e-6);

  test("grows with quality, size and count", () => {
    expect(price(generation("high"))).toBeGreaterThan(price(generation("medium")));
    expect(price(generation("medium", "2560x1440"))).toBeGreaterThan(price(generation("medium", "1536x864")));
    expect(price(generation("medium", "2560x1440", 3))).toBeGreaterThan(price(generation("medium", "2560x1440", 1)));
  });

  test("puts a high-quality 2560x1440 image well above GPT Image's per-megapixel rate", () => {
    expect(price(generation("high"))).toBeGreaterThan(0.4);
  });
});

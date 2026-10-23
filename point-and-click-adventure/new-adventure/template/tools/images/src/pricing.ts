// Per-token prices for a gateway model, from the gateway's public model list.
import type { Pricing } from "./run-request";

/** GPT Image 2.x prices on the gateway (2026-10-10), used when the list is unreachable. */
export const FALLBACK_PRICING: Pricing = { inputUsdPerToken: 5e-6, outputUsdPerToken: 30e-6 };

export async function fetchPricing(model: string): Promise<Pricing & { source: "gateway" | "fallback" }> {
  try {
    const response = await fetch("https://ai-gateway.vercel.sh/v1/models");
    const body = (await response.json()) as { data?: { id: string; pricing?: { input?: string; output?: string } }[] };
    const pricing = body.data?.find((entry) => entry.id === model)?.pricing;
    if (pricing?.input && pricing?.output) {
      return { inputUsdPerToken: Number(pricing.input), outputUsdPerToken: Number(pricing.output), source: "gateway" };
    }
  } catch {
    // Offline or the list changed shape: use the fallback below.
  }
  return { ...FALLBACK_PRICING, source: "fallback" };
}

// Confirms the gateway credential works and the GPT Image models are listed,
// without generating anything. Usage, from the repository root:
//   bun tools/images/check.ts
import { gateway } from "ai";
import { credentialUsable, currentCredential, describeCredential } from "./src/credentials";
import { fetchPricing } from "./src/pricing";

const MODELS = ["openai/gpt-image-2.5-flare", "openai/gpt-image-2.5-sunburst", "openai/gpt-image-2"];

for (const model of MODELS) {
  const pricing = await fetchPricing(model);
  console.log(`${model}: ${pricing.source === "gateway" ? "listed" : "NOT LISTED"} ($${(pricing.outputUsdPerToken * 1e6).toFixed(2)}/M output tokens)`);
}

const credential = currentCredential();
console.log(describeCredential(credential));
if (!credentialUsable(credential)) process.exit(4);

try {
  const credits = await gateway.getCredits();
  console.log(`gateway credits: balance $${credits.balance}, used $${credits.totalUsed}`);
} catch (error) {
  console.error(`gateway authentication failed: ${(error as Error).message}`);
  process.exit(5);
}

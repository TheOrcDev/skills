import { expect, test } from "bun:test";
import { ElevenLabs } from "../src/client";

const noSleep = async () => {};

test("a missing key is refused before any request", () => {
  expect(() => new ElevenLabs({ apiKey: "" })).toThrow("ELEVENLABS_API_KEY");
});

test("HTTP 429 backs off, honouring Retry-After, then succeeds", async () => {
  const waits: number[] = [];
  let calls = 0;
  const client = new ElevenLabs({
    apiKey: "test-key",
    sleep: async (ms) => void waits.push(ms),
    fetch: async (_url: string, init: RequestInit) => {
      calls++;
      expect((init.headers as Record<string, string>)["xi-api-key"]).toBe("test-key");
      return calls < 3 ? new Response("", { status: 429, headers: calls === 1 ? { "retry-after": "2" } : {} }) : new Response("{}", { status: 200 });
    },
  });
  const response = await client.request("/v1/x");
  expect(response.status).toBe(200);
  expect(calls).toBe(3);
  expect(waits).toEqual([2000, 2000]);
});

test("it gives up after its retries and returns the 429", async () => {
  let calls = 0;
  const client = new ElevenLabs({ apiKey: "k", maxRetries: 2, sleep: noSleep, fetch: async () => (calls++, new Response("", { status: 429 })) });
  expect((await client.request("/v1/x")).status).toBe(429);
  expect(calls).toBe(3);
});

test("no more than `concurrency` requests run at once", async () => {
  let inFlight = 0;
  let most = 0;
  const client = new ElevenLabs({
    apiKey: "k",
    concurrency: 3,
    fetch: async () => {
      inFlight++;
      most = Math.max(most, inFlight);
      await new Promise((done) => setTimeout(done, 10));
      inFlight--;
      return new Response("{}", { status: 200 });
    },
  });
  await Promise.all(Array.from({ length: 10 }, () => client.request("/v1/x")));
  expect(most).toBe(3);
});

test("the subscription report reads the endpoint", async () => {
  const client = new ElevenLabs({
    apiKey: "k",
    fetch: async (url: string) => {
      expect(url).toBe("https://api.elevenlabs.io/v1/user/subscription");
      return Response.json({ tier: "creator", character_count: 1200, character_limit: 100000 });
    },
  });
  expect(await client.subscription()).toEqual({ tier: "creator", character_count: 1200, character_limit: 100000 });
});

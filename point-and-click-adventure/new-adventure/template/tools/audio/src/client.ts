// The ElevenLabs API client (audio-pipeline.md §3): at most `concurrency`
// requests at once, and HTTP 429 backs off and retries (Retry-After when the
// server gives one). The key comes from ELEVENLABS_API_KEY in the operator's
// .env and is never printed.

export const BASE_URL = "https://api.elevenlabs.io";
/** Concurrent requests allowed per plan tier. */
export const CONCURRENCY: Record<string, number> = { free: 2, starter: 3, creator: 5, pro: 10, scale: 15, business: 15 };

export interface Subscription {
  tier: string;
  character_count: number;
  character_limit: number;
  next_character_count_reset_unix?: number;
}

export type Fetcher = (url: string, init: RequestInit) => Promise<Response>;

export interface ClientOptions {
  apiKey: string;
  concurrency?: number;
  maxRetries?: number;
  baseUrl?: string;
  fetch?: Fetcher;
  sleep?: (ms: number) => Promise<void>;
}

export class ElevenLabs {
  private active = 0;
  private waiting: (() => void)[] = [];
  private readonly concurrency: number;
  private readonly maxRetries: number;
  private readonly baseUrl: string;
  private readonly fetcher: Fetcher;
  private readonly sleep: (ms: number) => Promise<void>;

  constructor(private readonly options: ClientOptions) {
    if (!options.apiKey) throw new Error("ELEVENLABS_API_KEY is not set: the operator puts it in .env");
    this.concurrency = options.concurrency ?? CONCURRENCY.free;
    this.maxRetries = options.maxRetries ?? 5;
    this.baseUrl = options.baseUrl ?? BASE_URL;
    this.fetcher = options.fetch ?? ((url, init) => fetch(url, init));
    this.sleep = options.sleep ?? ((ms) => new Promise((done) => setTimeout(done, ms)));
  }

  /** Sends a request, waiting for a free slot and backing off on HTTP 429. */
  async request(path: string, init: RequestInit = {}): Promise<Response> {
    await this.acquire();
    try {
      for (let attempt = 0; ; attempt++) {
        const response = await this.fetcher(`${this.baseUrl}${path}`, {
          ...init,
          headers: { ...(init.headers as Record<string, string>), "xi-api-key": this.options.apiKey },
        });
        if (response.status !== 429 || attempt >= this.maxRetries) return response;
        const header = response.headers.get("retry-after");
        const retryAfter = header === null ? Number.NaN : Number(header);
        await this.sleep(Number.isFinite(retryAfter) && retryAfter >= 0 ? retryAfter * 1000 : Math.min(1000 * 2 ** attempt, 30_000));
      }
    } finally {
      this.release();
    }
  }

  async subscription(): Promise<Subscription> {
    const response = await this.request("/v1/user/subscription");
    if (!response.ok) throw new Error(`subscription: HTTP ${response.status}`);
    return (await response.json()) as Subscription;
  }

  private async acquire(): Promise<void> {
    if (this.active < this.concurrency) {
      this.active++;
      return;
    }
    await new Promise<void>((resume) => this.waiting.push(resume));
  }

  private release(): void {
    const next = this.waiting.shift();
    if (next) next();
    else this.active--;
  }
}

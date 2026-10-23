// The request-hash cache (audio-pipeline.md §3): a request's result is kept
// under its hash, and the same hash never calls the API again unless forced.

import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

export class RequestCache {
  constructor(private readonly dir: string) {}

  path(hash: string): string {
    return join(this.dir, `${hash}.bin`);
  }

  has(hash: string): boolean {
    return existsSync(this.path(hash));
  }

  /** The cached result, or what `call` returns (then kept). */
  async get(hash: string, call: () => Promise<Uint8Array>, force = false): Promise<{ bytes: Uint8Array; cached: boolean }> {
    if (!force && this.has(hash)) return { bytes: new Uint8Array(readFileSync(this.path(hash))), cached: true };
    const bytes = await call();
    mkdirSync(this.dir, { recursive: true });
    writeFileSync(this.path(hash), bytes);
    return { bytes, cached: false };
  }
}

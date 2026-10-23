// Serves build/web for local browser checks.
// Usage: bun tools/build/serve.ts [port]
import { join, resolve } from "node:path";

const root = resolve(import.meta.dir, "..", "..", "build", "web");
const port = Number(process.argv[2] ?? 8060);

const contentTypes: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".wasm": "application/wasm",
  ".pck": "application/octet-stream",
  ".png": "image/png",
  ".webp": "image/webp",
  ".svg": "image/svg+xml",
  ".json": "application/json",
};

Bun.serve({
  port,
  async fetch(request) {
    const pathname = decodeURIComponent(new URL(request.url).pathname);
    const full = resolve(root, "." + (pathname === "/" ? "/index.html" : pathname));
    if (!full.startsWith(root + "/")) {
      return new Response("Forbidden", { status: 403 });
    }
    const file = Bun.file(full);
    if (!(await file.exists())) {
      return new Response("Not found", { status: 404 });
    }
    const extension = full.slice(full.lastIndexOf("."));
    return new Response(file, {
      headers: {
        "Content-Type": contentTypes[extension] ?? "application/octet-stream",
        "Cache-Control": "no-store",
      },
    });
  },
});

console.log(`Serving ${join(root)} at http://localhost:${port}/`);

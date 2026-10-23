// Runs a QA scenario of the browser build in a visible Chrome window and
// prints the game's [qa] lines, plus console errors, uncaught exceptions and
// page crashes. Sound is allowed from the start, as after a player's first click. Automation tabs are often hidden, and hidden
// tabs throttle requestAnimationFrame, so frame times only mean something in a
// window like this one. It uses a throwaway profile and closes when done.
//
// Usage (with `bun tools/build/serve.ts` running):
//   bun tools/build/browser-qa.ts [scenario=perf] [canvas=1920x1080] [passes=2] [shots-dir]
// QA_BASE_URL checks a deployed build instead, e.g. https://<project>.vercel.app.
// With a shots-dir, each screenshot the scenario takes is also captured from
// the page into that folder, since the game's own land in the browser's storage.
// A capture lands a moment after the game's own shot, so motion may have moved on.
// The window is sized so the canvas has that many device pixels. Each pass
// loads the page again, with qa-pass=<n> in the URL; later passes run with warm
// caches, so they are the ones to quote.
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PORT = 9333;
const TIMEOUT_MS = 180_000;

const scenario = process.argv[2] ?? "perf";
const [canvasW, canvasH] = (process.argv[3] ?? "1920x1080").split("x").map(Number);
const passes = Number(process.argv[4] ?? 2);
const shotsDir = process.argv[5];
if (shotsDir) mkdirSync(shotsDir, { recursive: true });
const captures: Promise<void>[] = [];
const baseUrl = new URL(process.env.QA_BASE_URL ?? "http://localhost:8060/");
const pageUrl = `${baseUrl.origin}/?qa=${scenario}`;

const profile = mkdtempSync(join(tmpdir(), "adventure-chrome-"));
// Retina Macs draw two device pixels per CSS pixel; --app windows add a ~28 px title bar.
const scale = 2;
const chrome = Bun.spawn(
  [
    CHROME,
    `--user-data-dir=${profile}`,
    `--remote-debugging-port=${PORT}`,
    "--no-first-run",
    "--no-default-browser-check",
    // Keep a fresh profile's background work from stealing frames.
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-default-apps",
    "--disable-extensions",
    "--disable-sync",
    "--disable-features=Translate,OptimizationHints,MediaRouter",
    // macOS counts a window that others cover as hidden, and Chrome then stops
    // requestAnimationFrame: the game freezes until the window shows again.
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
    "--disable-background-timer-throttling",
    // A page plays no sound until the player's first click, and nothing here
    // clicks: let it play from the start, as it can after that click.
    "--autoplay-policy=no-user-gesture-required",
    `--window-size=${canvasW / scale},${canvasH / scale + 28}`,
    "--window-position=40,40",
    `--app=${pageUrl}`,
  ],
  { stdout: "ignore", stderr: "ignore" },
);

async function pageSocketUrl(): Promise<string> {
  const deadline = Date.now() + 20_000;
  while (Date.now() < deadline) {
    try {
      const targets = (await (await fetch(`http://127.0.0.1:${PORT}/json`)).json()) as { type: string; url: string; webSocketDebuggerUrl: string }[];
      const page = targets.find((t) => t.type === "page" && t.url.startsWith(baseUrl.origin));
      if (page) return page.webSocketDebuggerUrl;
    } catch {
      // Chrome is still starting.
    }
    await Bun.sleep(250);
  }
  throw new Error("Chrome's debugging endpoint did not come up");
}

let exitCode = 1;
try {
  const socket = new WebSocket(await pageSocketUrl());
  let nextId = 1;
  const pending = new Map<number, (value: unknown) => void>();
  const send = (method: string, params: object = {}) =>
    new Promise<any>((resolve) => {
      const id = nextId++;
      pending.set(id, resolve);
      socket.send(JSON.stringify({ id, method, params }));
    });
  let pass = 1;
  let passed = true;
  const done = new Promise<void>((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`no [qa] RESULT within ${(TIMEOUT_MS * passes) / 1000} s`)), TIMEOUT_MS * passes);
    socket.onmessage = (event) => {
      const message = JSON.parse(String(event.data));
      if (message.id && pending.has(message.id)) {
        pending.get(message.id)!(message.result);
        pending.delete(message.id);
      } else if (message.method === "Runtime.consoleAPICalled") {
        const text = message.params.args.map((a: { value?: unknown }) => String(a.value ?? "")).join(" ");
        if (text.includes("[qa]")) {
          console.log(`[pass ${pass}] ${text}`);
          const shot = shotsDir && text.match(/PASS screenshot .*\/([^/]+)\.png/)?.[1];
          if (shot) {
            const name = `pass${pass}-${shot}.png`;
            captures.push(send("Page.captureScreenshot", { format: "png" }).then((result) => writeFileSync(join(shotsDir, name), Buffer.from(result.data, "base64"))));
          }
          if (text.includes("[qa] RESULT")) {
            passed &&= text.includes("RESULT PASS");
            if (pass >= passes) {
              exitCode = passed ? 0 : 1;
              clearTimeout(timer);
              resolve();
            } else {
              pass += 1;
              send("Page.navigate", { url: `${pageUrl}&qa-pass=${pass}` });
            }
          }
        } else if (message.params.type === "error") {
          console.log(`[pass ${pass}] [console error] ${text.slice(0, 400)}`);
        }
      } else if (message.method === "Runtime.exceptionThrown") {
        const details = message.params.exceptionDetails;
        console.log(`[pass ${pass}] [exception] ${String(details.exception?.description ?? details.text).slice(0, 400)}`);
      } else if (message.method === "Inspector.targetCrashed") {
        console.log(`[pass ${pass}] [crashed] the page crashed`);
      }
    };
  });
  await new Promise((resolve) => (socket.onopen = resolve));
  await send("Runtime.enable");
  await send("Page.enable");
  await send("Inspector.enable");
  const page = await send("Runtime.evaluate", {
    expression: "JSON.stringify({hidden: document.hidden, dpr: devicePixelRatio})",
    returnByValue: true,
  });
  console.log(`[browser] ${page.result.value}`);
  await done;
  await Promise.all(captures);
  socket.close();
} catch (error) {
  console.error(`[browser] ${error instanceof Error ? error.message : error}`);
} finally {
  chrome.kill();
  await chrome.exited;
  rmSync(profile, { recursive: true, force: true });
}
process.exit(exitCode);

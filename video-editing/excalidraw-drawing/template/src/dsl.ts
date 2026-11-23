// Scene vocabulary. Times are absolute seconds in the source video.
// Build every element at module level: rough.js seeds come from a counter,
// so creating drawables inside a render would make strokes jitter each frame.
import type { Drawable } from "roughjs/bin/core";
import { C, R, arrow, check } from "./sketch";

export type S = { k: "s"; dr: Drawable[]; at: number; dur: number; fill?: number };
export type T = {
  k: "t";
  at: number;
  dur?: number;
  x: number;
  y: number;
  size: number;
  text: string;
  color?: string;
  font?: "hand" | "code";
  anchor?: "start" | "middle";
  fadeAt?: number; // fade the text out (e.g. when it is replaced)
};
export type El = S | T;

/** Sketch one or more drawables on over `dur` seconds. `fill` = hachure opacity. */
export const s = (dr: Drawable | Drawable[], at: number, dur: number, fill?: number): S => ({
  k: "s",
  dr: Array.isArray(dr) ? dr : [dr],
  at,
  dur,
  fill,
});

/** Handwritten text (Virgil). `y` is the baseline. */
export const hand = (text: string, x: number, y: number, size: number, at: number, o: Partial<T> = {}): T => ({
  k: "t",
  text,
  x,
  y,
  size,
  at,
  ...o,
});

/** Code text (Cascadia). `y` is the baseline. */
export const code = (text: string, x: number, y: number, size: number, at: number, o: Partial<T> = {}): T => ({
  k: "t",
  text,
  x,
  y,
  size,
  at,
  font: "code",
  ...o,
});

/** Numbered step badge: a circle with the number written in. */
export const badge = (n: number, cx: number, cy: number, at: number, color = C.blue): El[] => [
  s(R.ellipse(cx, cy, 46, 46, { stroke: color, strokeWidth: 2.6 }), at, 0.35),
  hand(String(n), cx, cy + 10, 28, at + 0.25, { anchor: "middle", color, dur: 0.2 }),
];

/** Terminal command box: ink rect, green `$`, Cascadia command. */
export const terminal = (cmd: string, x: number, y: number, w: number, at: number, size = 24): El[] => [
  s(R.rect(x, y, w, 62), at, 0.5),
  code("$", x + 19, y + 39, size, at + 0.4, { color: C.green, dur: 0.1 }),
  code(cmd, x + 45, y + 39, size, at + 0.5, { dur: Math.max(0.6, cmd.length * 0.07) }),
];

/** File with a folded corner (yellow) and its name in Cascadia. */
export const file = (name: string, x: number, y: number, w: number, at: number): El[] => [
  s(
    [
      R.poly([[x, y], [x + w - 22, y], [x + w, y + 22], [x + w, y + 62], [x, y + 62]], { stroke: C.yellow }),
      R.lin([[x + w - 22, y], [x + w - 22, y + 22], [x + w, y + 22]], { stroke: C.yellow, strokeWidth: 1.8 }),
    ],
    at,
    0.55,
  ),
  code(name, x + 15, y + 40, 19, at + 0.55, { color: C.yellow, dur: Math.max(0.5, name.length * 0.065) }),
];

/** Hachure-filled box (violet by default): packages, definitions, modules. */
export const filledBox = (x: number, y: number, w: number, h: number, at: number, color = C.violet, opacity = 0.2) =>
  s(R.rect(x, y, w, h, { stroke: color, fill: color, fillStyle: "hachure" }), at, 0.55, opacity);

/** Straight arrow with an optional small muted label above its middle. */
export const labeledArrow = (x1: number, y1: number, x2: number, y2: number, at: number, label?: string): El[] => [
  s(arrow([[x1, y1], [x2, y2]]), at, 0.35),
  ...(label ? [hand(label, Math.min(x1, x2) + 12, Math.min(y1, y2) - 16, 19, at + 0.1, { color: C.muted })] : []),
];

/** Browser/app window: frame, title bar line, three dots. */
export const uiWindow = (x: number, y: number, w: number, h: number, at: number): El[] => [
  s(R.rect(x, y, w, h), at, 0.5),
  s(R.line(x, y + 28, x + w, y + 28, { strokeWidth: 1.8 }), at + 0.45, 0.2),
  s([17, 31, 45].map((dx) => R.ellipse(x + dx, y + 14, 7, 7, { strokeWidth: 1.6, roughness: 0.4 })), at + 0.6, 0.2),
];

/** Stick figure (a user), centered on x, head at y. */
export const person = (x: number, y: number, at: number, label?: string): El[] => [
  s(
    [
      R.ellipse(x, y, 20, 20, { strokeWidth: 2, roughness: 0.6 }),
      R.lin([[x, y + 10], [x, y + 40]], { strokeWidth: 2 }),
      R.lin([[x - 13, y + 22], [x, y + 18], [x + 13, y + 22]], { strokeWidth: 2 }),
      R.lin([[x - 11, y + 62], [x, y + 40], [x + 11, y + 62]], { strokeWidth: 2 }),
    ],
    at,
    0.6,
  ),
  ...(label ? [hand(label, x, y + 90, 18, at + 0.5, { color: C.muted, anchor: "middle", dur: 0.35 })] : []),
];

/** Green tick, drawn on. */
export const tick = (x: number, y: number, at: number, scale = 1) => s(check(x, y, scale), at, 0.25);

/** Bracket under a span (x1..x2) with a label under its point: "both must pass". */
export const brace = (x1: number, x2: number, y: number, at: number, label: string, color = C.green): El[] => {
  const m = (x1 + x2) / 2;
  return [
    s(R.lin([[x1, y], [x1 + 6, y + 14], [m - 8, y + 14], [m, y + 27], [m + 8, y + 14], [x2 - 6, y + 14], [x2, y]], { stroke: color }), at, 0.5),
    hand(label, m, y + 57, 24, at + 0.3, { color, anchor: "middle", dur: Math.max(0.5, label.length * 0.05) }),
  ];
};

/** Warning triangle (red), top point at (x, y). */
export const warning = (x: number, y: number, at: number) =>
  s([R.poly([[x, y], [x + 16, y + 28], [x - 16, y + 28]], { stroke: C.red, strokeWidth: 2.2, roughness: 0.6 }), R.line(x, y + 9, x, y + 19, { stroke: C.red, strokeWidth: 2.2 })], at, 0.3);

/** Location pin (blue), centered on x, head at y. */
export const pin = (x: number, y: number, at: number) =>
  s([R.ellipse(x, y, 18, 18, { stroke: C.blue, strokeWidth: 2.4, roughness: 0.5 }), R.lin([[x, y + 9], [x, y + 18]], { stroke: C.blue, strokeWidth: 2.4 })], at, 0.3);

export { C, R, arrow, check };

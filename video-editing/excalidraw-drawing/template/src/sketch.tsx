import React from "react";
import rough from "roughjs";
import type { Drawable, Options } from "roughjs/bin/core";

// Excalidraw dark-mode palette (lightened, as Excalidraw renders them on dark).
export const C = {
  ink: "#e9ecef",
  muted: "#9aa0a6",
  blue: "#74c0fc",
  green: "#8ce99a",
  yellow: "#ffe066",
  violet: "#b197fc",
  red: "#ff8787",
};

const gen = rough.generator();
let seed = 7;
const base = (o: Options = {}): Options => ({
  roughness: 1,
  bowing: 1,
  strokeWidth: 2.4,
  stroke: C.ink,
  hachureGap: 9,
  fillWeight: 1.3,
  hachureAngle: -41,
  seed: seed++,
  ...o,
});

export const R = {
  rect: (x: number, y: number, w: number, h: number, o?: Options) => gen.rectangle(x, y, w, h, base(o)),
  ellipse: (cx: number, cy: number, w: number, h: number, o?: Options) => gen.ellipse(cx, cy, w, h, base(o)),
  line: (x1: number, y1: number, x2: number, y2: number, o?: Options) => gen.line(x1, y1, x2, y2, base(o)),
  poly: (pts: [number, number][], o?: Options) => gen.polygon(pts, base(o)),
  lin: (pts: [number, number][], o?: Options) => gen.linearPath(pts, base(o)),
  curve: (pts: [number, number][], o?: Options) => gen.curve(pts, base(o)),
};

// An arrow is a shaft followed by its head; the head points along the last segment.
export const arrow = (pts: [number, number][], o: Options = {}): Drawable[] => {
  const shaft = pts.length > 2 ? R.curve(pts, o) : R.line(pts[0][0], pts[0][1], pts[1][0], pts[1][1], o);
  const [ax, ay] = pts[pts.length - 2];
  const [bx, by] = pts[pts.length - 1];
  const a = Math.atan2(by - ay, bx - ax);
  const L = 16;
  const h1: [number, number] = [bx - L * Math.cos(a - 0.45), by - L * Math.sin(a - 0.45)];
  const h2: [number, number] = [bx - L * Math.cos(a + 0.45), by - L * Math.sin(a + 0.45)];
  return [shaft, R.lin([h1, [bx, by], h2], { ...o, roughness: 0.6 })];
};

export const check = (x: number, y: number, s = 1, o: Options = {}) =>
  R.lin([[x, y], [x + 8 * s, y + 9 * s], [x + 24 * s, y - 12 * s]], { stroke: C.green, strokeWidth: 3, roughness: 0.6, ...o });

type Seg = { d: string[]; stroke: string; width: number; fill: boolean };

// Split a drawable into strokes. Rough draws every line twice; the two passes
// are drawn together so the pen never seems to retrace.
const segments = (dr: Drawable): Seg[] => {
  const multi = !(dr.options.disableMultiStroke ?? false);
  const out: Seg[] = [];
  const fills: Seg[] = [];
  const infos = gen.toPaths(dr);
  dr.sets.forEach((set, i) => {
    const info = infos[i];
    const subs = info.d.split(/(?=M)/).filter((s) => s.trim());
    const isFill = set.type === "fillSketch";
    const step = multi && subs.length % 2 === 0 ? 2 : 1;
    for (let k = 0; k < subs.length; k += step) {
      (isFill ? fills : out).push({ d: subs.slice(k, k + step), stroke: info.stroke, width: info.strokeWidth, fill: isFill });
    }
  });
  return [...out, ...fills];
};

const ease = (p: number) => (p <= 0 ? 0 : p >= 1 ? 1 : 1 - Math.pow(1 - p, 2));

export const Sketch: React.FC<{ drawables: Drawable[]; t: number; at: number; dur: number; fillOpacity?: number; opacity?: number }> = ({
  drawables,
  t,
  at,
  dur,
  fillOpacity = 0.3,
  opacity = 1,
}) => {
  const segs = React.useMemo(() => drawables.flatMap(segments), [drawables]);
  if (t < at) return null;
  const strokes = segs.filter((s) => !s.fill).length;
  const fills = segs.length - strokes;
  // Outline gets 70% of the time, hachure fill scribbles in during the rest.
  const strokeDur = fills ? dur * 0.7 : dur;
  const fillDur = dur - strokeDur;
  let si = 0;
  let fi = 0;
  return (
    <g opacity={opacity}>
      {segs.map((s, i) => {
        let p: number;
        if (!s.fill) {
          const slot = strokeDur / strokes;
          p = ease((t - at - si * slot) / slot);
          si++;
        } else {
          const slot = fillDur / Math.max(1, fills);
          p = Math.min(1, Math.max(0, (t - at - strokeDur - fi * slot) / (slot * 3)));
          fi++;
        }
        if (p <= 0) return null;
        return (
          <g key={i} opacity={s.fill ? fillOpacity : 1}>
            {s.d.map((d, j) => (
              <path
                key={j}
                d={d}
                fill="none"
                stroke={s.stroke}
                strokeWidth={s.width}
                strokeLinecap="round"
                strokeLinejoin="round"
                pathLength={1}
                strokeDasharray={p >= 1 ? undefined : "1 1"}
                strokeDashoffset={p >= 1 ? undefined : 1 - p}
              />
            ))}
          </g>
        );
      })}
    </g>
  );
};

const CHAR_W = { hand: 0.56, code: 0.6 };

export const Hand: React.FC<{
  t: number;
  at: number;
  dur?: number;
  x: number;
  y: number;
  size: number;
  text: string;
  color?: string;
  font?: "hand" | "code";
  anchor?: "start" | "middle";
  fadeAt?: number;
  id: string;
}> = ({ t, at, dur, x, y, size, text, color = C.ink, font = "hand", anchor = "start", fadeAt, id }) => {
  if (t < at) return null;
  const d = dur ?? Math.max(0.3, text.length * 0.05);
  const p = ease((t - at) / d);
  const w = text.length * size * CHAR_W[font] * 1.15;
  const left = anchor === "middle" ? x - w / 2 : x - 4;
  const fade = fadeAt === undefined ? 1 : Math.max(0, 1 - (t - fadeAt) / 0.3);
  if (fade <= 0) return null;
  return (
    <g opacity={fade}>
      {p < 1 && (
        <clipPath id={id}>
          <rect x={left} y={y - size * 1.2} width={w * p} height={size * 1.7} />
        </clipPath>
      )}
      <text
        x={x}
        y={y}
        fontSize={size}
        fill={color}
        textAnchor={anchor}
        fontFamily={font === "hand" ? "Virgil" : "Cascadia"}
        clipPath={p < 1 ? `url(#${id})` : undefined}
      >
        {text}
      </text>
    </g>
  );
};

import React from "react";
import { AbsoluteFill, continueRender, delayRender, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { BOARD, BOARD_FRAME, KEEP_OUT } from "./config";
import { scene } from "./scene";
import { Hand, Sketch } from "./sketch";

const useFonts = () => {
  const [handle] = React.useState(() => delayRender("fonts"));
  React.useEffect(() => {
    Promise.all(
      [
        new FontFace("Virgil", `url(${staticFile("fonts/Virgil.woff2")})`),
        new FontFace("Cascadia", `url(${staticFile("fonts/Cascadia.woff2")})`),
      ].map((f) => f.load().then((ff) => document.fonts.add(ff))),
    ).then(() => continueRender(handle));
  }, [handle]);
};

// Transparent drawing layer. `guide` adds red dashed outlines of the board and keep-out zones.
export const Board: React.FC<{ guide?: boolean }> = ({ guide }) => {
  useFonts();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  if (frame < BOARD_FRAME) return <AbsoluteFill />;
  return (
    <AbsoluteFill>
      {/* position:absolute matters: a static <svg> paints under absolutely positioned siblings. */}
      <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0 }}>
        {scene.map((e, i) =>
          e.k === "s" ? (
            <Sketch key={i} drawables={e.dr} t={t} at={e.at} dur={e.dur} fillOpacity={e.fill} />
          ) : (
            <Hand key={i} id={`c${i}`} t={t} {...e} />
          ),
        )}
        {guide && (
          <g fill="none" stroke="#f03e3e" strokeDasharray="6 6">
            <rect x={BOARD.x} y={BOARD.y} width={BOARD.w} height={BOARD.h} />
            {KEEP_OUT.map((b, i) => (
              <rect key={i} x={b.x} y={b.y} width={b.w} height={b.h} />
            ))}
          </g>
        )}
      </svg>
    </AbsoluteFill>
  );
};

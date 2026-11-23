import React from "react";
import { Composition } from "remotion";
import { Board } from "./Board";
import { DURATION_S, FPS } from "./config";

const frames = Math.ceil(DURATION_S * FPS);

export const Root: React.FC = () => (
  <>
    <Composition id="Board" component={Board} durationInFrames={frames} fps={FPS} width={1920} height={1080} />
    <Composition id="Guide" component={Board} defaultProps={{ guide: true }} durationInFrames={frames} fps={FPS} width={1920} height={1080} />
  </>
);

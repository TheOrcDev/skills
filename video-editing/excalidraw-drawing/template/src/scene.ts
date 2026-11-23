// The drawing, cued to the narration. Replace this starter with the video's scene.
// Times are absolute seconds in the source video; take them from words.json and
// start each element 0.1-0.3s before the word that introduces it.
// A full worked example is examples/copybook-setup.scene.ts in the skill folder.
import { C, El, R, badge, file, hand, labeledArrow, s, terminal } from "./dsl";

export const scene: El[] = [
  // Title, written right after the board appears, with a yellow underline.
  hand("Setting up Copybook", 140, 140, 50, 20.5, { dur: 1.2 }),
  s(R.line(140, 158, 690, 154, { stroke: C.yellow, strokeWidth: 3 }), 21.7, 0.45),

  // Step 1: a command that writes a file.
  ...badge(1, 165, 229, 24.4),
  ...terminal("npx @copybook/cli init", 205, 198, 410, 24.6),
  ...labeledArrow(620, 229, 703, 229, 28.0, "writes"),
  ...file("copybook.config.ts", 712, 198, 235, 28.4),
];

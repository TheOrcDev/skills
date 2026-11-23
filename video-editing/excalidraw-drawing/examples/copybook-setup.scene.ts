// Worked example: the Copybook setup board (Videorc 9.mp4, 4K30, board on at frame 597).
// Copy over template/src/scene.ts to see the full style. config.ts in the template
// already holds this video's numbers. Every cue is the absolute second of the spoken word.
import { C, El, R, arrow, badge, check, code, hand, s } from "./dsl";

const W2 = -20; // section 2 x shift

export const scene: El[] = [
  // "So let's turn on our board so we can here draw it up"
  hand("Setting up Copybook", 140, 140, 50, 20.5, { dur: 1.2 }),
  s(R.line(140, 158, 690, 154, { stroke: C.yellow, strokeWidth: 3 }), 21.7, 0.45),

  // 1 — "we run our npx copybook cli init"
  ...badge(1, 165, 229, 24.4),
  s(R.rect(205, 198, 410, 62), 24.6, 0.5),
  code("$", 224, 237, 24, 25.0, { color: C.green, dur: 0.1 }),
  code("npx @copybook/cli init", 250, 237, 24, 25.1, { dur: 1.6 }),
  // "then it writes the copybook config.ts"
  s(arrow([[620, 229], [703, 229]]), 28.0, 0.4),
  hand("writes", 632, 213, 19, 28.1, { color: C.muted }),
  s(
    [
      R.poly([[712, 198], [925, 198], [947, 220], [947, 260], [712, 260]], { stroke: C.yellow }),
      R.lin([[925, 198], [925, 220], [947, 220]], { stroke: C.yellow, strokeWidth: 1.8 }),
    ],
    28.4,
    0.55,
  ),
  code("copybook.config.ts", 727, 238, 19, 28.95, { color: C.yellow, dur: 1.2 }),
  // "we install copybook core and copybook cli"
  s(arrow([[330, 264], [330, 318]]), 31.6, 0.3),
  s(arrow([[505, 264], [605, 318]]), 31.8, 0.3),
  hand("installs", 350, 300, 19, 31.8, { color: C.muted }),
  s(R.rect(205, 322, 250, 58, { stroke: C.violet, fill: C.violet, fillStyle: "hachure" }), 32.2, 0.6, 0.22),
  code("@copybook/core", 225, 358, 21, 32.6, { dur: 0.8 }),
  s(R.rect(490, 322, 240, 58, { stroke: C.violet, fill: C.violet, fillStyle: "hachure" }), 33.5, 0.6, 0.22),
  code("@copybook/cli", 510, 358, 21, 33.9, { dur: 0.8 }),
  // "and we set up coding agents"
  s(arrow([[468, 384], [468, 438]]), 35.0, 0.35),
  hand("sets up", 484, 418, 19, 35.1, { color: C.muted }),
  s(R.rect(205, 442, 740, 150, { stroke: C.green }), 35.3, 0.7),
  hand("coding agents", 225, 479, 26, 35.7, { color: C.green, dur: 0.7 }),
  // "agents md section"
  s(R.rect(225, 496, 215, 78), 36.6, 0.4),
  code("AGENTS.md", 241, 528, 20, 36.9, { dur: 0.6 }),
  hand("section", 241, 558, 20, 37.6, { color: C.muted }),
  // "copybook skill"
  s(R.rect(460, 496, 200, 78), 38.1, 0.4),
  hand("Copybook", 478, 529, 23, 38.3, { dur: 0.5 }),
  hand("skill", 478, 559, 23, 38.85, { dur: 0.3 }),
  // "and the copybook mcp server. So that's mcp.json."
  s(R.rect(680, 496, 245, 78), 39.8, 0.4),
  hand("MCP server", 698, 529, 23, 40.2, { dur: 0.7 }),
  code(".mcp.json", 698, 559, 19, 42.4, { color: C.blue, dur: 0.5 }),

  // 2 — "We find all the code snippets, shell commands, and coding agent prompts that UI shows to users"
  ...badge(2, 1032 + W2, 229, 43.8),
  s(R.rect(1075 + W2, 198, 300, 290), 44.0, 0.5),
  s(R.line(1075 + W2, 226, 1375 + W2, 226, { strokeWidth: 1.8 }), 44.45, 0.2),
  s([1092, 1106, 1120].map((x) => R.ellipse(x + W2, 212, 7, 7, { strokeWidth: 1.6, roughness: 0.4 })), 44.6, 0.2),
  s(R.rect(1092 + W2, 244, 266, 54, { stroke: C.muted }), 44.8, 0.3),
  code("const db = connect()", 1105 + W2, 277, 16, 45.0, { dur: 0.7, fadeAt: 62.2 }),
  s(R.rect(1092 + W2, 316, 266, 54, { stroke: C.muted }), 45.7, 0.3),
  code("$ npm i acme", 1105 + W2, 349, 16, 45.9, { dur: 0.5, fadeAt: 62.45 }),
  s(R.rect(1092 + W2, 388, 266, 54, { stroke: C.muted }), 47.0, 0.3),
  code('"Set up Acme with…"', 1105 + W2, 421, 16, 47.3, { dur: 0.8, fadeAt: 62.7 }),
  // a user looking at the UI
  s(
    [
      R.ellipse(1040 + W2, 404, 20, 20, { strokeWidth: 2, roughness: 0.6 }),
      R.lin([[1040 + W2, 414], [1040 + W2, 444]], { strokeWidth: 2 }),
      R.lin([[1027 + W2, 426], [1040 + W2, 422], [1053 + W2, 426]], { strokeWidth: 2 }),
      R.lin([[1029 + W2, 466], [1040 + W2, 444], [1051 + W2, 466]], { strokeWidth: 2 }),
    ],
    48.2,
    0.6,
  ),
  hand("users", 1040 + W2, 494, 18, 48.7, { color: C.muted, anchor: "middle", dur: 0.35 }),
  // "and move each one into a definition with defineSnippet, defineCommand, or definePrompt"
  s(arrow([[1362 + W2, 271], [1440 + W2, 271]]), 49.7, 0.3),
  s(arrow([[1362 + W2, 343], [1440 + W2, 343]]), 50.0, 0.3),
  s(arrow([[1362 + W2, 415], [1440 + W2, 415]]), 50.3, 0.3),
  s(R.rect(1446 + W2, 240, 240, 62, { stroke: C.violet, fill: C.violet, fillStyle: "hachure" }), 51.3, 0.55, 0.18),
  code("defineSnippet()", 1462 + W2, 266, 19, 51.95, { dur: 0.6 }),
  s(R.rect(1446 + W2, 312, 240, 62, { stroke: C.violet, fill: C.violet, fillStyle: "hachure" }), 52.6, 0.55, 0.18),
  code("defineCommand()", 1462 + W2, 338, 19, 53.2, { dur: 0.6 }),
  s(R.rect(1446 + W2, 384, 240, 62, { stroke: C.violet, fill: C.violet, fillStyle: "hachure" }), 53.7, 0.55, 0.18),
  code("definePrompt()", 1462 + W2, 410, 19, 54.3, { dur: 0.6 }),
  // "And each one gets its own dotted ID."
  code("console.connect.branch", 1462 + W2, 290, 13, 56.1, { color: C.green, dur: 0.6 }),
  code("console.install.cmd", 1462 + W2, 362, 13, 56.6, { color: C.green, dur: 0.6 }),
  code("console.create-project.agent", 1462 + W2, 434, 13, 57.1, { color: C.green, dur: 0.7 }),

  // 3 — "we render the definitions where the strings used to be with the same props"
  s(arrow([[1560 + W2, 452], [1520 + W2, 540], [1330 + W2, 548], [1222 + W2, 494]], { stroke: C.green }), 60.4, 0.9),
  ...badge(3, 1272 + W2, 612, 60.6, C.green),
  hand("render where the strings were", 1302 + W2, 621, 22, 61.0, { dur: 1.3 }),
  s(R.rect(1092 + W2, 244, 266, 54, { stroke: C.green }), 62.2, 0.3),
  hand("snippet definition", 1108 + W2, 278, 19, 62.4, { color: C.green, dur: 0.5 }),
  s(R.rect(1092 + W2, 316, 266, 54, { stroke: C.green }), 62.45, 0.3),
  hand("command definition", 1108 + W2, 350, 19, 62.65, { color: C.green, dur: 0.5 }),
  s(R.rect(1092 + W2, 388, 266, 54, { stroke: C.green }), 62.7, 0.3),
  hand("prompt definition", 1108 + W2, 422, 19, 62.9, { color: C.green, dur: 0.5 }),
  hand("with the same props", 1302 + W2, 656, 22, 63.4, { color: C.yellow, dur: 0.9 }),

  // 4 — "npx copybook snapshot, then npx copybook check, both must pass, and npx copybook status lists anything left to do"
  ...badge(4, 165, 692, 65.0),
  s(R.rect(205, 662, 300, 60), 65.2, 0.4),
  code("npx copybook snapshot", 222, 699, 19, 65.6, { dur: 1.0 }),
  s(arrow([[510, 692], [560, 692]]), 66.9, 0.3),
  s(R.rect(565, 662, 270, 60), 67.1, 0.4),
  code("npx copybook check", 582, 699, 19, 67.5, { dur: 0.9 }),
  s(R.lin([[210, 735], [216, 749], [512, 749], [520, 762], [528, 749], [824, 749], [830, 735]], { stroke: C.green }), 69.5, 0.5),
  hand("both must pass", 520, 792, 24, 69.8, { color: C.green, anchor: "middle", dur: 0.7 }),
  s(check(474, 690, 1), 70.1, 0.25),
  s(check(800, 690, 1), 70.35, 0.25),
  s(arrow([[840, 692], [890, 692]]), 70.8, 0.3),
  s(R.rect(895, 662, 290, 60), 71.0, 0.4),
  code("npx copybook status", 912, 699, 19, 71.4, { dur: 1.0 }),
  s(arrow([[1040, 726], [1040, 762]]), 73.0, 0.3),
  hand("anything left to do", 1040, 792, 22, 73.4, { anchor: "middle", dur: 1.3 }),

  // 5 — "we report which definitions we created, where they're shown, and anything that we couldn't migrate"
  ...badge(5, 165, 893, 75.9, C.yellow),
  s(R.rect(205, 850, 1040, 88, { stroke: C.yellow, fill: C.yellow, fillStyle: "hachure", hachureGap: 12 }), 76.2, 0.7, 0.12),
  hand("Report", 226, 904, 28, 76.7, { color: C.yellow, dur: 0.5 }),
  s(check(342, 893, 0.85), 77.6, 0.25),
  hand("definitions created", 372, 903, 22, 77.8, { dur: 0.9 }),
  s([R.ellipse(630, 892, 18, 18, { stroke: C.blue, strokeWidth: 2.4, roughness: 0.5 }), R.lin([[630, 901], [630, 910]], { stroke: C.blue, strokeWidth: 2.4 })], 79.3, 0.3),
  hand("where they're shown", 652, 903, 22, 79.4, { dur: 0.9 }),
  s([R.poly([[926, 878], [942, 906], [910, 906]], { stroke: C.red, strokeWidth: 2.2, roughness: 0.6 }), R.line(926, 887, 926, 897, { stroke: C.red, strokeWidth: 2.2 })], 81.6, 0.3),
  hand("couldn't migrate", 952, 903, 22, 81.8, { color: C.red, dur: 0.8 }),
];

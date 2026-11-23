# Style

The board look is Excalidraw on a dark canvas: hand-drawn rough.js strokes, Virgil handwriting, Cascadia for code, and Excalidraw's palette lightened the way it renders in dark mode. Every value below is already wired into `template/src/sketch.tsx` and `dsl.ts`, so use those and don't restyle.

## Tokens

| Token | Value | Use for |
|---|---|---|
| `C.ink` | `#e9ecef` | Default strokes and text: boxes, commands, body labels |
| `C.muted` | `#9aa0a6` | Arrow labels ("writes", "installs"), sub-labels, captions under figures, item outlines inside a window |
| `C.green` | `#8ce99a` | Success and outcomes: ticks, "both must pass", grouped results, things that got "rendered/done", `$` prompts, IDs |
| `C.yellow` | `#ffe066` | Files, the title underline, highlights, the final Report box, "same props"-style emphasis |
| `C.violet` | `#b197fc` | Packages, modules, definitions: hachure-filled boxes |
| `C.blue` | `#74c0fc` | Step badges, config values (`.mcp.json`), location pins |
| `C.red` | `#ff8787` | Failures, warnings, "couldn't migrate" |

- **Fonts.** Virgil for words, at 50 for the title, 22 to 28 for section text, 18 to 20 for small labels. Cascadia for anything typed (commands, file names, function names, IDs), at 24 for commands, 19 to 21 for names and 13 to 16 inside tight boxes.
- **Strokes.** Roughness 1 and bowing 1, double-stroked (the rough.js default). Width 2.4 for shapes, 3 for the title underline, 1.6 to 2 for small details.
- **Fills.** Hachure only, angle -41, gap 9 (12 for big boxes), opacity 0.12 to 0.25. No solid fills.
- **Canvas.** Author in 1920x1080 units and render at scale 2 for 4K. The board itself is the recording's own dark board, so never paint a background.

## Vocabulary (`dsl.ts`)

| Helper | Draws |
|---|---|
| `hand`, `code` | Text written left to right (y is the baseline) |
| `badge(n, cx, cy, at, color?)` | Numbered step circle, blue by default. Use green or yellow for the later steps that close a loop or report results |
| `terminal(cmd, x, y, w, at)` | Command box with a green `$` |
| `file(name, x, y, w, at)` | Yellow file with a folded corner |
| `filledBox(x, y, w, h, at, color?)` | Violet hachure box for packages and definitions |
| `labeledArrow(x1, y1, x2, y2, at, label?)` | Straight arrow with a small muted verb |
| `arrow(points)` via `s()` | Curved arrow through 3 or more points, for loops back ("render where the strings were") |
| `uiWindow(x, y, w, h, at)` | App or browser frame with a title bar and three dots |
| `person(x, y, at, label?)` | Stick figure ("users") |
| `brace(x1, x2, y, at, label)` | Bracket under a span with its label ("both must pass") |
| `tick`, `warning`, `pin` | Green check, red warning triangle, blue pin, for report lines |
| `R.rect/ellipse/line/poly/lin/curve` + `s()` | Anything else, in the same rough style |

Replacing something (raw string → definition): fade the old text with `fadeAt`, draw a green rect over the old outline, then write the new label in green.

## Layout grammar

- **Title** top-left, about 90px inside the board edge, at Virgil 50, with a yellow underline drawn just after it.
- **Sections** are numbered with badges and read left to right, then top to bottom, in spoken order. Step 1 goes top-left, step 2 top-right, and later steps run in rows down the left, away from the webcam.
- **Inside a section**, the flow runs left to right (command → arrow + verb → result), and branches go down (installs → two boxes side by side). Groups get a colored frame with a handwritten heading (green "coding agents").
- **Spacing**: 40 to 60px between blocks, 20px between sibling boxes, and 15 to 20px of padding inside boxes. Box heights are 58 to 62 for one line and about 78 for two.
- **The last step** (report, summary) is one wide yellow hachure box along the bottom, with its entries in a single row, each with an icon.
- Leave the space above the webcam for short annotations only, such as a loop label.

## Timing

- Shape outlines take 0.3 to 0.6s. Hachure scribbles in during the last 30%.
- Text is written at about 0.05s per character (0.3s minimum). Keep a command's text going for as long as it is being spoken.
- Start each element 0.1 to 0.3s before its word. Stagger siblings 0.25 to 0.5s apart, or one per word when they are listed aloud.
- Draw an arrow when its verb is said ("writes", "installs", "move into"), then the target.
- Nothing exits. The finished board stays up until the board leaves the shot.

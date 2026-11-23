// Per-video settings. Fill these in from the probe and find-cut steps in SKILL.md.
// Layout is authored in 1920x1080 units. Render with --scale=2 for a 4K source, --scale=1 for 1080p.

export const FPS = 30;
export const DURATION_S = 91.533; // ffprobe -show_entries format=duration
export const BOARD_FRAME = 597; // first frame the board is on screen (scripts/find-cut.py)

type Box = { x: number; y: number; w: number; h: number };

// The drawable board, in 1920x1080 units.
export const BOARD: Box = { x: 86, y: 35, w: 1620, h: 1000 };

// Never draw here: the webcam, the board's toolbar, window buttons.
export const KEEP_OUT: Box[] = [
  { x: 1277, y: 710, w: 429, h: 325 }, // webcam, bottom right
  { x: 710, y: 968, w: 373, h: 45 }, // board toolbar
  { x: 1500, y: 40, w: 200, h: 35 }, // board buttons, top right
];

# Video editing skills

Skills for OrcDev video: scripting, cutting and posting, plus overlays, drawings and other post-production passes on a finished take. Each skill is one folder with a `SKILL.md`, plus any templates or scripts it needs beside it.

| Skill | Purpose |
|---|---|
| [short-format-video](short-format-video/SKILL.md) | End-to-end Shorts: voice, script package, beat-by-beat shot list, Remotion edit, posting, Drive and Notion log, 60-day repost. Companions: [RULES.md](short-format-video/RULES.md), [WORKFLOW.md](short-format-video/WORKFLOW.md) |
| [excalidraw-drawing](excalidraw-drawing/SKILL.md) | Excalidraw-style diagram drawn onto the on-screen board in sync with the narration, composited over untouched footage |

![Excalidraw drawing example](excalidraw-drawing/examples/copybook-setup.jpg)

## Coming to this collection

More video skills will land here as siblings, one folder each:

- `long-format-video` for full-length YouTube videos
- further formats (livestream segments, tutorials, trailers) as they are needed

## Adding a skill

Keep the same shape: `video-editing/<skill-id>/SKILL.md`, companion files beside it when needed, an entry in the root `registry.json` that lists every file, and a row in the table above.

## Installation

Install a skill with the Skills CLI or the shadcn registry. Choose one:

```bash
npx skills add TheOrcDev/skills --full-depth --skill short-format-video
npx shadcn@latest add TheOrcDev/skills/short-format-video
```

```bash
npx skills add TheOrcDev/skills --full-depth --skill excalidraw-drawing
npx shadcn@latest add TheOrcDev/skills/excalidraw-drawing
```

Use `--full-depth`, because the Skills CLI's default discovery stops at the repository's `skills/` collection. Full-depth discovery also includes `video-editing/` and `game-dev/`. The shadcn entries target `~/.claude/skills/<name>/`, the same as the rest of the repository.

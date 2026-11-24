# Video skills

Skills for scripting, planning, cutting and posting OrcDev video content. Each skill is one folder with a `SKILL.md`; supporting references or scripts sit beside it when a skill needs them.

| Format | Skill | Purpose |
|---|---|---|
| Short format (TikTok, Reels, YouTube Shorts) | [short-format-video](short-format-video/SKILL.md) | End-to-end Shorts: voice, script package, beat-by-beat shot list, Remotion edit, posting, Drive and Notion log, 60-day repost. Companions: [RULES.md](short-format-video/RULES.md), [WORKFLOW.md](short-format-video/WORKFLOW.md) |

## Coming to this collection

More video skills will land here as siblings of `short-format-video`, one folder each:

- `long-format-video` for full-length YouTube videos
- further formats (livestream segments, tutorials, trailers) as they are needed

Keep the same shape when adding one: `videos/<skill-id>/SKILL.md`, companion files beside it when needed, an entry in the root `registry.json` that lists every file, and a row in the table above.

## Installation

Install a skill with the Skills CLI or the shadcn registry. Choose one:

```bash
npx skills add TheOrcDev/skills --full-depth --skill short-format-video
npx shadcn@latest add TheOrcDev/skills/short-format-video
```

Use `--full-depth` because the Skills CLI's default local discovery stops after finding this repository's `skills/` collection. Full-depth discovery also includes `videos/` and `game-dev/`. The shadcn entries target `~/.claude/skills/<name>/`, the same as the rest of the repository.

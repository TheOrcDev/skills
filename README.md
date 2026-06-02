# skills

A [shadcn registry](https://ui.shadcn.com/docs/registry/github) of Claude Code skills. Install any skill straight from this repo with the shadcn CLI — no separate registry server needed.

## Install a skill

```bash
npx shadcn@latest add TheOrcDev/skills/orc-me
```

This writes the skill into `.claude/skills/orc-me/SKILL.md` in your current project.

### Preview before installing

```bash
npx shadcn@latest view TheOrcDev/skills/orc-me        # inspect the payload
npx shadcn@latest add TheOrcDev/skills/orc-me --dry-run
```

### Pin to a version

```bash
npx shadcn@latest add TheOrcDev/skills/orc-me#v1.0.0
```

## Available skills

| Skill    | Description                                                          |
| -------- | ------------------------------------------------------------------- |
| `orc-me` | Orc voice mode — blunt, decisive, no-hedging answers (accuracy kept) |

## Repo layout

```
registry.json          # registry manifest — lists every skill as an item
skills/
  orc-me/
    SKILL.md           # the skill itself
```

## Add your own skill

1. Create `skills/<name>/SKILL.md` with frontmatter (`name`, `description`) and a body.
2. Add an item to `registry.json` pointing `path` at the file and `target` at `~/.claude/skills/<name>/SKILL.md`.
3. Validate: `npx shadcn@latest registry validate TheOrcDev/skills`.
4. Commit and push — it's instantly installable.

# Game development skills

Six project-specific skills from [Final Stand](https://github.com/TheOrcDev/finalstand), copied from [commit 23c230a](https://github.com/TheOrcDev/finalstand/commit/23c230ac10e83d2a3317e4642995af15ec2e696a). The skill files are preserved with their companion workflows and rules. `rig-it` is the portable seventh: the same rigging and animation loop rebuilt around a per-subject contract with its Blender tooling bundled, so it does not need a Final Stand checkout.

| Stage | Skill | Supporting files |
|---|---|---|
| Reference art | [game-art-reference-packs](game-art-reference-packs/SKILL.md) | [Workflow](game-art-reference-packs/WORKFLOW.md) |
| Geometry and texturing | [meshy-asset-production](meshy-asset-production/SKILL.md) | [Workflow](meshy-asset-production/WORKFLOW.md) |
| Model cleanup | [game-model-cleanup](game-model-cleanup/SKILL.md) | [Workflow](game-model-cleanup/WORKFLOW.md) |
| Creature animation | [creature-animation](creature-animation/SKILL.md) | [Rules](creature-animation/RULES.md), [workflow](creature-animation/WORKFLOW.md) |
| Humanoid animation | [humanoid-animation](humanoid-animation/SKILL.md) | [Rules](humanoid-animation/RULES.md), [workflow](humanoid-animation/WORKFLOW.md) |
| Unity integration | [unity-asset-integration](unity-asset-integration/SKILL.md) | [Workflow](unity-asset-integration/WORKFLOW.md) |
| Portable rigging and animation | [rig-it](rig-it/SKILL.md) | [Rules](rig-it/RULES.md), [workflow](rig-it/WORKFLOW.md), [references](rig-it/references/), Blender scripts in `scripts/` |

## Requirements and scope

These instructions reference Final Stand's `ArtSource/3D` contracts, `tools/3d` scripts, Unity editor installers, production plans and coordination board. Those tools and game assets are not bundled in this repository. Run the workflows from a compatible Final Stand checkout, or adapt the project paths and contracts before using them in another game.

The animation skills retain the original environment paths, provider observations and plan-specific settings. Resolve the actual installed Blender/Unity versions, available browser tools, current Meshy settings and existing spend authorization before executing them. Installing a skill does not authorize paid generation or approve game art.

## Installation

Install individual skills using the repository's existing CLI conventions:

```bash
npx skills add TheOrcDev/skills --full-depth --skill game-model-cleanup
npx shadcn@latest add TheOrcDev/skills/game-model-cleanup
```

Choose one installation method. To install the complete collection with the Skills CLI:

```bash
for skill in game-art-reference-packs meshy-asset-production game-model-cleanup creature-animation humanoid-animation unity-asset-integration; do
  npx skills add TheOrcDev/skills --full-depth --skill "$skill" || break
done
```

Use `--full-depth` because the Skills CLI's default local discovery stops after finding this repository's existing `skills/` collection. Full-depth discovery also includes `game-dev/`.

Each skill has an entry in the root `registry.json`, including every supporting Markdown file. The shadcn entries target `~/.claude/skills/<name>/` consistently with the existing collection. Keep skill folders together so the relative handoff links between skills resolve; when installing just one skill, install its companion skill when that stage is needed.

## Updating this collection

Compare changes against `.claude/skills/` in Final Stand, copy all changed supporting files, and update the source commit above. Validate skill frontmatter, relative links and registry file mappings. Keep project-specific budgets and acceptance rules in the source project contracts rather than inventing new defaults in this distribution.

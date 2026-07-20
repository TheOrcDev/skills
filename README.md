# 🪓 Orc Skills

> **WAAAGH!** Battle-ready agent skills, forged by [TheOrcDev](https://github.com/TheOrcDev).

Blunt tools for warchiefs who want work done. Install through the Skills CLI for any supported agent, or use the shadcn command to drop a skill into Claude Code. Zug zug.

## 🪓 The Horde

### `orc-me` - orc voice mode

Makes Claude blunt, decisive, no hedging. Leads with the answer, picks a side, cuts the padding — but keeps every command and code path exactly right. The voice is the delivery; **directness is the weapon**.

```bash
npx shadcn@latest add TheOrcDev/skills/orc-me
```

Wake it with `/orc-me`, "orc mode", or "talk like an orc." Say "normal mode" to stand it down.

### `war-boss-review` - orc code review

Blunt, zero-hedging review of your changes. Ranks every finding **KILL IT** (blocker), **WEAK** (minor), or **WAAAGH-WORTHY** (strong), strips the politeness padding, and forces a verdict: ship or hold the line.

```bash
npx shadcn@latest add TheOrcDev/skills/war-boss-review
```

Call it with `/war-boss-review`, "orc review", or "roast my code."

### `cut-it` - plan slicer

Takes a plan you already have and cuts it into ordered, self-contained slices — execution phases sized for an AI agent to pick up and run one at a time. Dependency-ordered, each slice verifiable and safe to commit.

```bash
npx shadcn@latest add TheOrcDev/skills/cut-it
```

Call it with `/cut-it`, "slice this plan", or "break this into phases."

### `auto-grill` - self-driving plan grill

Grills a plan one question at a time, but drives the interview itself: each question gets three answers (**A/B/C**) with one marked **✅ Recommended**, and it auto-answers with the recommended pick — looping down the decision tree until the plan is fully resolved. Review every auto-made decision in one pass and flip any you disagree with.

```bash
npx shadcn@latest add TheOrcDev/skills/auto-grill
```

Call it with `/auto-grill`, "auto-grill this plan", or "grill it and decide."

### `shadscan-pre-commit` - shadcn UI commit gate

Adds a deterministic Shadscan score gate before every commit. It detects the package manager and existing hook setup, takes a baseline, pins Shadscan locally, and preserves every command already in the hook.

Install for Codex, Claude Code, Cursor, and other supported agents:

```bash
npx skills add TheOrcDev/skills --skill shadscan-pre-commit
```

Install into Claude Code through the shadcn registry:

```bash
npx shadcn@latest add TheOrcDev/skills/shadscan-pre-commit
```

Call it with `$shadscan-pre-commit`, "add Shadscan before every commit", or "set up a Shadscan commit gate."

---

**Lok'tar Ogar!** 🪓

---
name: cut-it
description: Cut an existing plan into ordered, self-contained slices (execution phases) sized for an AI agent to pick up and run one at a time. Each slice is dependency-ordered, independently verifiable, and leaves the codebase working. Use when the user has a plan, spec, PRD, or approved design and says "cut it", "cut-it", "slice this plan", "break this into phases", "split into workable parts", or invokes /cut-it.
---

# Cut It

Take a plan that already exists and **cut it into clean slices** — ordered phases an AI agent can pick up and execute one at a time. Each slice is a workable, verifiable chunk that leaves the codebase running. The flavor is orc; the slices stay clean and precise — an agent must execute them cold.

## 1. Find the plan — do not invent one

Work from a plan that already exists. Look in this order:

1. The plan in this conversation — an approved design, plan-mode output, a decision just reached.
2. A file or ticket the user points to — `PLAN.md`, a GitHub issue, a PRD, a doc.
3. If none is clear, ask the warchief to point at it or paste it. **Never fabricate the plan.**

Read the whole thing first. Name the end goal, the moving parts, and what depends on what.

## 2. Cut into slices

Rules for every cut:

- **Vertical, not horizontal.** Each slice delivers something that works end-to-end, not a half-built layer.
- **Dependency-ordered.** Foundations first. No slice depends on a later slice.
- **One agent run each.** Small enough to execute and verify in a single focused session; big enough to matter. Split a fat slice; merge a trivial one.
- **Always green.** Each slice leaves the codebase building, tests passing, app running — a safe commit point.
- **Self-contained.** Readable cold, with real file paths and commands. No reliance on this conversation.

## 3. Write each slice

```
## Slice N — <short imperative title>
**Goal:** one line — what this slice delivers.
**Depends on:** Slice X, Slice Y   (or: none)
**Touches:** files / modules / areas to create or change.
**Steps:**
  1. concrete action
  2. concrete action
**Done when:** the explicit, verifiable check — a test passes, a command prints X, the behavior works.
**Out of scope:** what NOT to do here, so the agent stays in its lane.
```

`Done when` is the most important line — it is how the agent knows the slice is finished.

## 4. Hand it off

- Open with the **battle order**: numbered slice titles and their dependencies, so the shape is clear at a glance.
- Then the full slices, in execution order.
- Offer to save them to a file (`PLAN.md` or `.claude/plans/<name>.md`) so an agent can pick them up, or to feed them to `/to-issues`.

## Guardrails

- Slice the real plan. If it is vague, sharpen it or ask — do not paper over gaps.
- Every slice independently verifiable, with no forward dependencies.
- Concrete over clever: real paths, real commands, real acceptance checks.
- If the plan is too big for clean slicing, say so and propose where to split the work.

---
name: anti-slop-checklist
description: Anti-slop rules for building UI with AI agents. Use when building or reviewing landing pages, components or any UI so the result doesn't look like generic AI output.
---

# Anti-slop checklist

Follow these rules when building UI. Run the checklist before calling the work done.

## Process

- Start from a reference: a screenshot plus what the user likes about it. Never "build me something".
- Write a short brief first: what it does, who it's for, 3 words it should feel like and 3 it shouldn't.
- Start from blocks (shadcn blocks or a component library) and compose them. Don't rebuild what a chosen block already provides.
- After building, screenshot desktop and mobile, list what's wrong (spacing, hierarchy, contrast, copy), fix it, repeat.

## Visual

- No default purple or blue-to-pink gradients unless the brand uses them.
- No glow, blur and glassmorphism on everything. Use effects only where they mean something.
- No cards inside cards. One level of containers is enough.
- No emoji as icons and no decorative emoji in headings.
- One accent color, one type scale, spacing on a 4 or 8 px grid.
- One primary action per section. Real visual hierarchy, not three equal buttons.
- Check mobile and dark mode, not just desktop.

## Content

- Code snippets must actually run, and the copy button must copy them.
- Install commands must be exactly right.
- The hero says what the product does and who it's for, above the fold.
- Never invent stats, testimonials, "trusted by" logos, GitHub numbers or people's names.
- Every link and button goes somewhere real. No "#" links or dead nav items.

## Copy

Inspired by Cursor's Unslop skill: https://github.com/cursor/plugins/blob/main/pstack/skills/unslop/SKILL.md

- Say what it does, not how it feels. Name the mechanism or a number.
- If a line could appear unchanged on another product's site, cut it.
- Never use: seamless, blazing fast, powerful, leverage, elevate, unlock, supercharge, delve, robust, cutting-edge, game-changer.
- No "Not just X, but Y". No forced groups of three.
- Plain words and active voice. "Use", not "leverage".
- Sentence case headings. No em dash overuse.
- No generic closers like "The future of X is here". End with the real next step.

## Before you ship

1. Is the code snippet real, and does copy work?
2. Is the install command exact?
3. Does the hero say what it is and who it's for?
4. Is any copy vague or full of AI words?
5. Any invented stats, testimonials, logos or names?
6. Did the AI rebuild something a block already provides?
7. Did you check mobile and dark mode?

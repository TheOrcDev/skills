---
name: anti-slop-checklist
description: Anti-slop rules for building UI with AI agents. Use when building or reviewing landing pages, components or any UI so the result doesn't look like generic AI output.
---

# Anti-slop checklist

Follow these rules when building UI. Run the checklist before calling the work done.

## Visual

- No default purple or blue-to-pink gradients unless the brand uses them.
- No glow, blur and glassmorphism on everything. Use effects only where they mean something.
- No cards inside cards. One level of containers is enough.
- No emoji as icons and no decorative emoji in headings.
- One accent color, one type scale, spacing on a 4 or 8 px grid.
- One primary action per section. Real visual hierarchy, not three equal buttons.
- No gradient text on every heading.
- No rounded-2xl on everything. Pick one radius and stick to it.
- No identical 3-column feature grid with an icon in a circle as the default layout.
- No floating blobs, orbs or random grid backgrounds as decoration.
- No pill badge above every heading ("✨ New").
- Enough contrast. No light gray text on white or dark gray on black.
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

## Review

- Reuse existing components instead of rebuilding them.
- Screenshot desktop and mobile, list what's wrong (spacing, hierarchy, contrast, copy), fix it, repeat.

## Before you ship

1. Is the code snippet real, and does copy work?
2. Is the install command exact?
3. Does the hero say what it is and who it's for?
4. Is any copy vague or full of AI words?
5. Any invented stats, testimonials, logos or names?
6. Any purple gradients, cards in cards, emoji icons or other visual tells?
7. Did you check mobile and dark mode?

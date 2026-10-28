---
name: anti-slop-checklist
description: Anti-slop rules for AI agents building or reviewing UI. Use before shipping a landing page or any AI-generated interface, or when the user says "anti-slop", "check for slop", or "does this look AI-made".
---

# Anti-slop checklist

Rules for the agent so the UI it builds does not look generic or AI-made. Run through them before calling a page done. Add new rules to the list below as we find them.

## Start from a reference

- Do not build from "build me something". Ask for a reference (a screenshot plus context: what the product is, who uses it, what the screen is for).
- Start from prebuilt blocks or complete pages when they exist. Do not rebuild something the chosen block already provides.

## Content

- The code snippet is real. It runs for this tool, and the copy button copies it.
- The install command is exactly right (package name, package manager, flags).
- The hero says what the tool does and who it is for, above the fold.
- Feature copy says what each feature does. No vague filler like "blazing fast", "powerful" or "seamless".
- No invented stats, testimonials, "trusted by" logos or GitHub numbers. Use real data or leave it out.

## Review loop

- Screenshot the result and critique it like a senior product designer. Return concrete changes only.
- Compare against the reference, then fix the differences.

## Rules to add

- (add new anti-slop rules here)

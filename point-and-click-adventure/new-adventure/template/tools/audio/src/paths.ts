import { resolve } from "node:path";

/** Repository root, from tools/audio/src. */
export const repoRoot = resolve(import.meta.dir, "..", "..", "..");
export const dialogueDir = resolve(repoRoot, "content/dialogue");
export const audioSource = resolve(repoRoot, "audio-source");
export const manifestPath = resolve(audioSource, "voice/manifest.json");
export const lockPath = resolve(audioSource, "voice/lock.json");
export const cacheDir = resolve(audioSource, "cache");
export const mastersDir = resolve(audioSource, "voice/masters");
export const postPath = resolve(audioSource, "voice/post.json");
/** The game's voice lines and their envelope table, in the Godot project. */
export const voiceDir = resolve(repoRoot, "assets/audio/voice/en");
export const envelopesPath = resolve(voiceDir, "envelopes.gd");
export const configPath = resolve(import.meta.dir, "..", "config.json");

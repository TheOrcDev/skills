// The voice manifest (`extract`) and what `voice` would generate: manifest
// lines new or changed since the lock (audio-pipeline.md §3, §4.2).

import { readdirSync, readFileSync } from "node:fs";
import { join, relative } from "node:path";
import { spokenLines, type SpokenLine } from "./dialogue";
import { canonical, sha256 } from "./hash";

export interface ManifestEntry extends SpokenLine {
  /** Repository-relative .dialogue file. */
  file: string;
  /** Hash of what is spoken: speaker, text and direction. A change regenerates
   * the line under the same id. */
  textHash: string;
}

export interface LockEntry {
  textHash: string;
  [key: string]: unknown;
}

export interface Diff {
  added: string[];
  changed: string[];
  removed: string[];
  unchanged: string[];
}

export function entry(line: SpokenLine, file: string): ManifestEntry {
  return { ...line, file, textHash: sha256(canonical({ speaker: line.speaker, text: line.text, direction: line.direction })) };
}

/** Every spoken line under `dir`, sorted by id; a repeated id is an error. */
export function buildManifest(dir: string, root: string, player: string): ManifestEntry[] {
  const entries: ManifestEntry[] = [];
  const seen = new Map<string, string>();
  for (const name of readdirSync(dir, { recursive: true }) as string[]) {
    if (!name.endsWith(".dialogue")) continue;
    const path = join(dir, name);
    const file = relative(root, path);
    for (const line of spokenLines(readFileSync(path, "utf8"), player)) {
      if (seen.has(line.id)) throw new Error(`${line.id} is in both ${seen.get(line.id)} and ${file}:${line.line}`);
      seen.set(line.id, `${file}:${line.line}`);
      entries.push(entry(line, file));
    }
  }
  return entries.sort((a, b) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
}

export function diff(manifest: ManifestEntry[], lock: Record<string, LockEntry>): Diff {
  const result: Diff = { added: [], changed: [], removed: [], unchanged: [] };
  const ids = new Set(manifest.map((e) => e.id));
  for (const e of manifest) {
    const locked = lock[e.id];
    if (!locked) result.added.push(e.id);
    else if (locked.textHash !== e.textHash) result.changed.push(e.id);
    else result.unchanged.push(e.id);
  }
  result.removed = Object.keys(lock).filter((id) => !ids.has(id)).sort();
  return result;
}

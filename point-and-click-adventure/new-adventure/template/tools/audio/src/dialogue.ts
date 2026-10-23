// Reads the spoken lines out of Dialogue Manager files (audio-pipeline.md §3,
// `extract`). Checked against Dialogue Manager 4.1.0: a line is
// `Speaker: text`, a response is `- text`, `% ` marks one of several random
// lines, `[ID:…]` is the static id, `[#a, #b=c]` are tags (voice direction is
// the `vo` tag, `[#vo=whispers]`), and `[if … /]` is a condition.

export interface SpokenLine {
  id: string;
  speaker: string;
  text: string;
  /** The `vo` tag's value, such as "whispers", or "". */
  direction: string;
  /** 1-based line number in the file. */
  line: number;
}

const ID = /\[ID:(.*?)\]/;
const TAGS = /\[#(.*?)\]/g;
const CONDITION = /\[(?:if|while)\s[^\]]*?\/\]/g;
const SPEAKER = /^([^:\[\]]+?):\s*(.*)$/;
const NOT_SPOKEN = /^(~|=>|=><|do |do!|set |if |elif |else|while |match |when |import |using |#)/;

/** The tags on a line: `[#a, #b=c]` gives ["a", "b=c"]. */
export function tags(raw: string): string[] {
  const result: string[] = [];
  for (const match of raw.matchAll(TAGS)) {
    for (const tag of match[1].split(",")) {
      const clean = tag.trim().replace(/^#/, "");
      if (clean && !result.includes(clean)) result.push(clean);
    }
  }
  return result;
}

/** The value of `name=value` among a line's tags, or "". */
export function tagValue(lineTags: string[], name: string): string {
  const found = lineTags.find((tag) => tag.startsWith(`${name}=`));
  return found ? found.slice(name.length + 1).trim() : "";
}

/** The spoken lines of one .dialogue file. Responses are spoken by `player`. */
export function spokenLines(source: string, player: string): SpokenLine[] {
  const lines: SpokenLine[] = [];
  source.split("\n").forEach((rawLine, index) => {
    let text = rawLine.trim();
    if (!text || NOT_SPOKEN.test(text)) return;
    const id = text.match(ID)?.[1]?.trim();
    if (!id) return;
    const lineTags = tags(text);
    text = text.replace(ID, "").replace(TAGS, "").replace(CONDITION, "").trim();
    let speaker = player;
    if (text.startsWith("- ")) {
      text = text.slice(2).trim();
    } else {
      if (text.startsWith("% ")) text = text.slice(2).trim();
      const said = text.match(SPEAKER);
      if (!said) return;
      speaker = said[1].trim();
      text = said[2].trim();
    }
    lines.push({ id, speaker, text: text.replace(/\s+/g, " "), direction: tagValue(lineTags, "vo"), line: index + 1 });
  });
  return lines;
}

import { expect, test } from "bun:test";
import { spokenLines, tagValue, tags } from "../src/dialogue";

const SOURCE = `~ start

# A comment, not spoken.
Gatekeeper: Halt. Who goes there? [#vo=booming] [ID:GK_HALT]
- Who are you? [if not GameState.get_flag("asked") /] [ID:UK_WHO]
	do GameState.set_flag("asked")
	Gatekeeper: Stone. [#calm, #vo=low] [ID:GK_STONE]
	=> start
% Hero: Nothing remarkable. [ID:UK_RANDOM_1]
Hero: A line without an id is skipped until \`ids\` gives it one.
=> END
`;

test("reads speakers, text, direction and ids, and skips what isn't spoken", () => {
  const lines = spokenLines(SOURCE, "Hero");
  expect(lines.map((l) => [l.id, l.speaker, l.text, l.direction])).toEqual([
    ["GK_HALT", "Gatekeeper", "Halt. Who goes there?", "booming"],
    ["UK_WHO", "Hero", "Who are you?", ""],
    ["GK_STONE", "Gatekeeper", "Stone.", "low"],
    ["UK_RANDOM_1", "Hero", "Nothing remarkable.", ""],
  ]);
  expect(lines[0].line).toBe(4);
});

test("tags follow Dialogue Manager's [#a, #b=c] form", () => {
  expect(tags("Hi [#happy, #vo=whispers] there [#loud]")).toEqual(["happy", "vo=whispers", "loud"]);
  expect(tagValue(["happy", "vo=whispers"], "vo")).toBe("whispers");
  expect(tagValue(["happy"], "vo")).toBe("");
});

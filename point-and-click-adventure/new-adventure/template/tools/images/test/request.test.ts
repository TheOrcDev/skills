import { describe, expect, test } from "bun:test";
import { parseRequest, RequestError, validateSize, withDeliveryRow, withStatus } from "../src/request";
import { requestText } from "./fixtures";

const root = process.cwd();

describe("parseRequest", () => {
  test("reads the header, generation block and prompt", () => {
    const request = parseRequest(requestText(), root);
    expect(request.id).toBe("IMG-0007");
    expect(request.title).toBe("Harbour steps, now");
    expect(request.status).toBe("open");
    expect(request.plan).toBe("002");
    expect(request.operatorApproval).toBe("required");
    expect(request.generation).toEqual({
      model: "openai/gpt-image-2.5-flare",
      size: "2560x1440",
      quality: "medium",
      n: 2,
      background: "opaque",
      references: [],
      mask: null,
    });
    expect(request.prompt).toBe("A ruined stone harbour stair, monochrome, heavy fog.");
  });

  test("rejects an empty prompt", () => {
    expect(() => parseRequest(requestText({ prompt: "…" }), root)).toThrow(RequestError);
  });

  test("rejects a missing reference file", () => {
    expect(() => parseRequest(requestText({ generation: { references: ["nope/missing.png"] } }), root)).toThrow("file not found");
  });

  test("rejects a mask without references", () => {
    expect(() => parseRequest(requestText({ generation: { mask: "package.json" } }), root)).toThrow("needs at least one reference");
  });

  test("rejects an unknown quality", () => {
    expect(() => parseRequest(requestText({ generation: { quality: "ultra" } }), root)).toThrow("quality");
  });
});

describe("validateSize", () => {
  test("accepts the room and vista sizes", () => {
    for (const size of ["2560x1440", "1536x864", "3840x1280", "1024x1024"]) expect(() => validateSize(size)).not.toThrow();
  });

  test("rejects sizes outside the GPT Image 2.5 rules", () => {
    expect(() => validateSize("1920x1080")).toThrow("multiples of 16");
    expect(() => validateSize("3840x1072")).toThrow("aspect");
    expect(() => validateSize("4096x2048")).toThrow("3840");
    expect(() => validateSize("512x512")).toThrow("pixel count");
  });
});

describe("request updates", () => {
  test("withStatus changes only the status line", () => {
    expect(withStatus(requestText(), "delivered")).toContain("status: delivered\n");
  });

  test("withDeliveryRow appends under the Delivery table, not the Review table", () => {
    const text = withDeliveryRow(withDeliveryRow(requestText(), ["1", "a"]), ["2", "b"]);
    const delivery = text.slice(text.indexOf("## Delivery"), text.indexOf("## Review"));
    expect(delivery).toContain("| 1 | a |\n| 2 | b |");
    expect(text.slice(text.indexOf("## Review"))).not.toContain("| 1 | a |");
  });
});

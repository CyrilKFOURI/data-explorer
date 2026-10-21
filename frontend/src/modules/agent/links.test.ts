import { describe, expect, it } from "vitest";

import { describePage, safeMarkdown } from "./links";

describe("agent links", () => {
  it("keeps links inside the app and turns any other into plain text", () => {
    expect(safeMarkdown("See [Age](/d/abc123/variable/Age).")).toBe("See [Age](/d/abc123/variable/Age).");
    expect(safeMarkdown("[click](https://evil.example/?q=secret)")).toBe("click");
    expect(safeMarkdown("[x](//evil.example)")).toBe("x");
    const script = safeMarkdown("[x](javascript:alert(1))");
    expect(script).not.toMatch(/\]\(/); // no link left, only text
    expect(script).toBe("x)");
  });

  it("describes the page the user is on", () => {
    expect(describePage("/d/abc/compare", { x: "Sex", y: "Age" })).toBe("Compare (x = Sex, y = Age)");
    expect(describePage("/d/abc", {})).toBe("Overview");
    expect(describePage("/settings", {})).toBeNull();
  });
});

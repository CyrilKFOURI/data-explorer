import { describe, expect, it } from "vitest";

import { t, type MessageKey } from ".";

describe("t", () => {
  it("fills placeholders", () => {
    expect(t("ml.compare.selected", { count: "3" })).toBe("3 models");
  });

  it("shows a missing key instead of breaking the page", () => {
    expect(t("ml.option.unknown_value" as MessageKey)).toBe("ml.option.unknown_value");
  });
});

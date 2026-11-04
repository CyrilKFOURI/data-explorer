import { describe, expect, it } from "vitest";

import { baseName, formatBytes, formatCount, formatRelativeTime } from "./format";

describe("format", () => {
  it("formats counts, compacting large ones", () => {
    expect(formatCount(1234)).toBe("1,234");
    expect(formatCount(2_345_678)).toBe("2.3M");
    expect(formatCount(null)).toBe("—");
  });

  it("formats byte sizes", () => {
    expect(formatBytes(512)).toBe("512 B");
    expect(formatBytes(1536)).toBe("1.5 KB");
    expect(formatBytes(250 * 1024 * 1024)).toBe("250 MB");
  });

  it("formats relative times", () => {
    const now = Date.parse("2026-10-12T12:00:00Z");
    expect(formatRelativeTime("2026-10-12T11:59:30Z", now)).toBe("just now");
    expect(formatRelativeTime("2026-10-12T09:00:00Z", now)).toBe("3 hours ago");
    expect(formatRelativeTime("2026-10-11T12:00:00Z", now)).toBe("yesterday");
  });

  it("extracts the last path segment", () => {
    expect(baseName("C:\\data\\sales.csv")).toBe("sales.csv");
    expect(baseName("/data/folder/")).toBe("folder");
  });
});

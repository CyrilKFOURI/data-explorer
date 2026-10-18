import { describe, expect, it } from "vitest";

import { parseWindows, rolling } from "./Windows";

describe("rolling windows", () => {
  it("reads free windows from the URL", () => {
    expect(parseWindows("7,15")).toEqual([7, 15]);
    expect(parseWindows("10, 10, 1, 400, x, 12")).toEqual([10, 12]);
    expect(parseWindows(undefined)).toEqual([]);
  });

  it("matches the server's rolling rule (half a window required, gaps skipped)", () => {
    const { mean, std } = rolling([1, 2, null, 4, 5], 4, "trailing");
    expect(mean[0]).toBeNull();
    expect(mean[1]).toBeCloseTo(1.5);
    expect(mean[4]).toBeCloseTo(11 / 3);
    expect(std[1]).toBeCloseTo(Math.SQRT1_2);
    expect(rolling([1, 2, 3, 4, 5], 3, "centered").mean).toEqual([1.5, 2, 3, 4, 4.5]);
  });
});

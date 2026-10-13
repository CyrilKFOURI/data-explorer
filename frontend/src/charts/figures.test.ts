import { describe, expect, it } from "vitest";

import type { Chart } from "../api/client";
import { categoryBars, formatNumber, isHorizontal, withAlpha } from "./figures";

function chart(overrides: Partial<Chart> = {}): Chart {
  return {
    kind: "bars",
    view: "bars",
    views: ["bars"],
    rows: 100,
    missing: 0,
    distinct: 3,
    bars: [],
    others: null,
    ordered: false,
    bins: [],
    stats: null,
    box: null,
    step: null,
    steps: [],
    examples: [],
    duplicates: 0,
    message: null,
    ...overrides,
  } as Chart;
}

describe("category display rules", () => {
  it("appends Others and (missing) as muted bars", () => {
    const bars = categoryBars(
      chart({
        bars: [{ label: "FR", count: 50 }],
        others: { count: 30, categories: 4 },
        missing: 20,
      }),
    );

    expect(bars).toEqual([
      { label: "FR", count: 50 },
      { label: "Others (4)", count: 30, muted: true },
      { label: "(missing)", count: 20, muted: true },
    ]);
  });

  it("goes horizontal for long labels or many bars", () => {
    const short = Array.from({ length: 5 }, (_, i) => ({ label: `c${i}`, count: 1 }));
    const many = Array.from({ length: 9 }, (_, i) => ({ label: `c${i}`, count: 1 }));

    expect(isHorizontal(short, false)).toBe(false);
    expect(isHorizontal(many, false)).toBe(true);
    expect(isHorizontal([{ label: "a very long category name", count: 1 }], false)).toBe(true);
  });

  it("keeps ordered parts vertical (months, weekdays)", () => {
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"].map(
      (label) => ({ label, count: 1 }),
    );

    expect(isHorizontal(months, true)).toBe(false);
  });
});

describe("helpers", () => {
  it("formats numbers compactly", () => {
    expect(formatNumber(1234.567)).toBe("1,235");
    expect(formatNumber(3.14159)).toBe("3.14");
    expect(formatNumber(12_500_000)).toBe("1.25e+7");
    expect(formatNumber(null)).toBe("—");
  });

  it("converts hex colors to rgba for Plotly", () => {
    expect(withAlpha("#2f7d6d", 0.15)).toBe("rgba(47, 125, 109, 0.15)");
  });
});

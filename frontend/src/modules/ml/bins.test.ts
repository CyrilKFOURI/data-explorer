import { describe, expect, it } from "vitest";

import {
  classCounts,
  defaultNames,
  edgesFor,
  jenksEdges,
  namesFor,
  quantileEdges,
  roundEdges,
  smallClasses,
  unequal,
  widthEdges,
  type Shape,
} from "./bins";

/** What the API sends: quantile_disc at 0, 0.001 … 1 (values of the data). */
function shapeOf(values: number[]): Shape {
  const sorted = [...values].sort((a, b) => a - b);
  const n = sorted.length;
  const at = (level: number) => sorted[Math.max(0, Math.ceil(level * n) - 1)] as number;
  const quantiles = Array.from({ length: 1001 }, (_, i) => at(i / 1000));
  const equal_counts = Array.from({ length: 9 }, (_, j) => Array.from({ length: j + 1 }, (_, i) => at((i + 1) / (j + 2))));
  return {
    rows: n,
    min: sorted[0] as number,
    max: sorted[n - 1] as number,
    p1: quantiles[10] as number,
    p99: quantiles[990] as number,
    quantiles,
    equal_counts,
    sample: sorted,
    values: null,
  };
}

/** Exact rows per class, intervals (a, b]. */
function exact(values: number[], edges: number[]): number[] {
  const counts = new Array<number>(edges.length + 1).fill(0);
  for (const v of values) {
    let i = 0;
    while (i < edges.length && v > (edges[i] as number)) i++;
    counts[i] = (counts[i] as number) + 1;
  }
  return counts;
}

describe("cutting a number into classes", () => {
  it("equal counts: 3 000 uniform values give 1 000 ± 1 rows per class", () => {
    const values = Array.from({ length: 3000 }, (_, i) => (i * 7919) % 3000 + 0.5);
    const shape = shapeOf(values);

    const edges = quantileEdges(shape, 3);

    for (const count of exact(values, edges)) expect(Math.abs(count - 1000)).toBeLessThanOrEqual(1);
    for (const count of classCounts(shape, edges)) expect(Math.abs(count - 1000)).toBeLessThanOrEqual(5);
  });

  it("natural breaks find the gaps", () => {
    expect(jenksEdges([1, 2, 3, 10, 11, 12, 30, 31], 3)).toEqual([3, 12]);
  });

  it("ties never cut one value in two: empty classes merge and the inequality is told", () => {
    const values = [
      ...Array.from({ length: 700 }, () => 10_000),
      ...Array.from({ length: 150 }, (_, i) => 5_000 + i),
      ...Array.from({ length: 150 }, (_, i) => 20_000 + i),
    ];
    const shape = shapeOf(values);

    const edges = quantileEdges(shape, 4);

    expect(edges.length).toBeLessThan(3); // merged
    expect(edges).toContain(10_000);
    const counts = exact(values, edges);
    expect(counts.reduce((a, b) => a + b, 0)).toBe(1000);
    expect(unequal(counts)).toBe(true);
  });

  it("rounds limits to round numbers", () => {
    expect(roundEdges([12487.33, 20912.8])).toEqual([12000, 21000]);
    expect(roundEdges([1234, 1240])).toEqual([1230, 1240]); // 3 digits when 2 would merge
  });

  it("equal width ignores outliers by default", () => {
    const values = [...Array.from({ length: 990 }, (_, i) => i / 10), 10_000];
    const shape = shapeOf(values);

    expect(widthEdges(shape, 2, false)[0]).toBeCloseTo(5000, 0);
    expect(widthEdges(shape, 2, true)[0]).toBeLessThan(100);
  });

  it("names, small classes and one class per value", () => {
    expect(defaultNames(3)).toEqual(["Low", "Medium", "High"]);
    expect(defaultNames(5)[0]).toBe("Very low");
    expect(defaultNames(7)[6]).toBe("Class 7");
    expect(smallClasses([500, 480, 20])).toEqual([2]);

    const rating: Shape = { ...shapeOf([1, 2, 3]), values: [1, 2, 3, 4, 5].map((value) => ({ value, count: 100 })) };
    const setup = { k: 5, method: "values" as const, round: true, ignoreOutliers: true, names: { 4: "Top" }, edges: null };
    const edges = edgesFor(setup, rating);
    expect(edges).toEqual([1, 2, 3, 4]);
    expect(classCounts(rating, edges)).toEqual([100, 100, 100, 100, 100]);
    expect(namesFor(setup, 5, rating, String)).toEqual(["1", "2", "3", "4", "Top"]);
  });
});

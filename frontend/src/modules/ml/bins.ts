/** Cutting a numeric target into ordered classes (018), in the browser so the preview follows
 *  every click. The API gives 1 001 exact quantiles (one per 0.1 % of the rows), a sorted sample
 *  and, for few distinct values, each value with its count. Intervals are (a, b]. */

export type BinMethod = "quantile" | "width" | "jenks" | "custom" | "values";

export type Shape = {
  rows: number;
  min: number | null;
  max: number | null;
  p1: number | null;
  p99: number | null;
  quantiles: number[];
  equal_counts: number[][]; // [k - 2]: exact equal-count limits for k = 2 … 10
  sample: number[];
  values: { value: number; count: number }[] | null;
};

export const MIN_CLASSES = 2;
export const MAX_CLASSES = 10;
const JENKS_POINTS = 1_000;

const NAMES: Record<number, string[]> = {
  2: ["Low", "High"],
  3: ["Low", "Medium", "High"],
  4: ["Low", "Medium-low", "Medium-high", "High"],
  5: ["Very low", "Low", "Medium", "High", "Very high"],
};

export function defaultNames(k: number): string[] {
  return NAMES[k] ?? Array.from({ length: k }, (_, i) => `Class ${i + 1}`);
}

/** Strictly increasing limits strictly inside [min, max): a limit at the maximum would leave an
 *  empty last class, two equal limits an empty class between them (merged). */
function clean(edges: number[], min: number, max: number): number[] {
  const sorted = [...edges].filter((e) => Number.isFinite(e)).sort((a, b) => a - b);
  return sorted.filter((e, i) => e >= min && e < max && (i === 0 || e > (sorted[i - 1] as number)));
}

/** Equal counts: the quantiles at 1/k, 2/k… A limit is a value of the data, so it never cuts
 *  one value in two; with many ties, classes merge or come out unequal. */
export function quantileEdges(shape: Shape, k: number): number[] {
  const { quantiles } = shape;
  const last = quantiles.length - 1;
  if (last < 1) return [];
  const edges =
    shape.equal_counts[k - 2] ?? Array.from({ length: k - 1 }, (_, i) => quantiles[Math.round(((i + 1) * last) / k)] as number);
  return clean(edges, quantiles[0] as number, quantiles[last] as number);
}

/** Equal width, from min to max, or between the 1st and 99th percentiles when outliers are
 *  ignored (the extremes then fall in the first and last classes). */
export function widthEdges(shape: Shape, k: number, ignoreOutliers: boolean): number[] {
  if (shape.min === null || shape.max === null) return [];
  const low = ignoreOutliers && shape.p1 !== null ? shape.p1 : shape.min;
  const high = ignoreOutliers && shape.p99 !== null ? shape.p99 : shape.max;
  const step = (high - low) / k;
  return clean(
    Array.from({ length: k - 1 }, (_, i) => low + step * (i + 1)),
    shape.min,
    shape.max,
  );
}

/** Natural breaks: exact Fisher–Jenks (dynamic programming minimising the within-class sum of
 *  squares) on at most 1 000 values taken evenly from the sorted sample. */
export function jenksEdges(sorted: number[], k: number): number[] {
  let data = sorted;
  if (sorted.length > JENKS_POINTS) {
    data = Array.from({ length: JENKS_POINTS }, (_, i) => sorted[Math.round((i * (sorted.length - 1)) / (JENKS_POINTS - 1))] as number);
  }
  const n = data.length;
  if (n === 0) return [];
  const classes = Math.min(k, n);
  const sum = new Float64Array(n + 1);
  const squares = new Float64Array(n + 1);
  for (let i = 0; i < n; i++) {
    const v = data[i] as number;
    sum[i + 1] = (sum[i] as number) + v;
    squares[i + 1] = (squares[i] as number) + v * v;
  }
  // cost of one class holding data[i..j] (inclusive)
  const cost = (i: number, j: number) => {
    const count = j - i + 1;
    const s = (sum[j + 1] as number) - (sum[i] as number);
    return (squares[j + 1] as number) - (squares[i] as number) - (s * s) / count;
  };
  // best[c][j]: lowest cost of data[0..j] in c + 1 classes; start[c][j]: where the last class begins
  const best: Float64Array[] = [];
  const start: Int32Array[] = [];
  best.push(Float64Array.from({ length: n }, (_, j) => cost(0, j)));
  start.push(new Int32Array(n));
  for (let c = 1; c < classes; c++) {
    const row = new Float64Array(n).fill(Infinity);
    const from = new Int32Array(n);
    const previous = best[c - 1] as Float64Array;
    for (let j = c; j < n; j++) {
      for (let i = c; i <= j; i++) {
        const value = (previous[i - 1] as number) + cost(i, j);
        if (value < (row[j] as number)) {
          row[j] = value;
          from[j] = i;
        }
      }
    }
    best.push(row);
    start.push(from);
  }
  const edges: number[] = [];
  let end = n - 1;
  for (let c = classes - 1; c > 0; c--) {
    const begin = (start[c] as Int32Array)[end] as number;
    edges.unshift(data[begin - 1] as number);
    end = begin - 1;
  }
  return clean(edges, data[0] as number, data[n - 1] as number);
}

/** One class per distinct value (a 1–5 rating: 5 classes). */
export function valueEdges(values: number[]): number[] {
  return values.slice(0, -1);
}

function significant(value: number, digits: number): number {
  if (value === 0) return 0;
  return Number(value.toPrecision(digits));
}

/** Round limits to 2 significant digits, 3 when two of them would merge, else keep them. */
export function roundEdges(edges: number[]): number[] {
  for (const digits of [2, 3]) {
    const rounded = edges.map((e) => significant(e, digits));
    if (rounded.every((e, i) => i === 0 || e > (rounded[i - 1] as number))) return rounded;
  }
  return edges;
}

/** Rows per class: exact from the value counts when given, else estimated on the quantile grid
 *  (each of the 1 001 points stands for 0.1 % of the rows). */
export function classCounts(shape: Shape, edges: number[]): number[] {
  const counts = new Array<number>(edges.length + 1).fill(0);
  const index = (value: number) => {
    let i = 0;
    while (i < edges.length && value > (edges[i] as number)) i++;
    return i;
  };
  if (shape.values) {
    for (const { value, count } of shape.values) counts[index(value)] = (counts[index(value)] as number) + count;
    return counts;
  }
  if (shape.quantiles.length === 0) return counts;
  const share = shape.rows / shape.quantiles.length;
  for (const q of shape.quantiles) counts[index(q)] = (counts[index(q)] as number) + share;
  return counts.map((c) => Math.round(c));
}

/** Classes too small to learn: under 5 % of the rows or under 30 rows. */
export function smallClasses(counts: number[]): number[] {
  const total = counts.reduce((a, b) => a + b, 0);
  return counts.flatMap((count, i) => (total && (count < 30 || count / total < 0.05) ? [i] : []));
}

/** Equal counts that are visibly unequal: ties at a limit. */
export function unequal(counts: number[]): boolean {
  const total = counts.reduce((a, b) => a + b, 0);
  if (!total) return false;
  return counts.some((c) => Math.abs(c / total - 1 / counts.length) > 0.02);
}

export type Setup = {
  k: number;
  method: BinMethod;
  round: boolean;
  ignoreOutliers: boolean;
  names: Record<number, string>; // names changed by the user, by position
  edges: number[] | null; // custom limits (or the limits of the run being shown)
};

export const DEFAULT_SETUP: Setup = { k: 3, method: "quantile", round: true, ignoreOutliers: true, names: {}, edges: null };

/** The limits a setup gives on this distribution. */
export function edgesFor(setup: Setup, shape: Shape): number[] {
  if (setup.edges) return clean(setup.edges, -Infinity, Infinity);
  const raw =
    setup.method === "width"
      ? widthEdges(shape, setup.k, setup.ignoreOutliers)
      : setup.method === "jenks"
        ? jenksEdges(shape.sample, setup.k)
        : setup.method === "values"
          ? valueEdges((shape.values ?? []).map((v) => v.value))
          : quantileEdges(shape, setup.k);
  if (!setup.round || setup.method === "values") return raw;
  return clean(roundEdges(raw), shape.min ?? -Infinity, shape.max ?? Infinity);
}

export function namesFor(setup: Setup, count: number, shape: Shape, format: (v: number) => string): string[] {
  const base =
    setup.method === "values" && shape.values && shape.values.length === count
      ? shape.values.map((v) => format(v.value))
      : defaultNames(count);
  const names = base.map((name, i) => setup.names[i]?.trim() || name);
  // names must stay distinct for the server
  return names.map((name, i) => (names.indexOf(name) === i ? name : `${name} ${i + 1}`));
}

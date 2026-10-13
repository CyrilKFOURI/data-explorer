import type { Normality, NormalityTest } from "../../api/client";
import { formatCount } from "../../lib/format";
import { t } from "../../lib/i18n";

export const ALPHAS = ["0.01", "0.05", "0.1"] as const;
export type Alpha = (typeof ALPHAS)[number];
/** Beyond this many values, tests detect departures too small to matter. */
const LARGE_SAMPLE = 5_000;

export function rejects(test: NormalityTest, alpha: number): boolean | null {
  return test.p_value === null ? null : test.p_value < alpha;
}

export function formatP(p: number | null): string {
  if (p === null) return "—";
  if (p < 0.001) return "< 0.001";
  return p.toFixed(p < 0.01 ? 4 : 3);
}

/** Some p-values are bounded by their method: Anderson's tables span 0.01–0.15, Lilliefors' Monte Carlo resolves 1/1000. */
const P_BOUNDS: Partial<Record<string, [number, number]>> = {
  anderson: [0.01, 0.15],
  lilliefors: [0.001, 1],
};

export function testP(test: NormalityTest): string {
  const bounds = P_BOUNDS[test.key];
  if (bounds && test.p_value !== null) {
    if (test.p_value <= bounds[0]) return `≤ ${bounds[0]}`;
    if (test.p_value >= bounds[1] && bounds[1] < 1) return `≥ ${bounds[1]}`;
  }
  return formatP(test.p_value);
}

/** "p = 0.034", "p < 0.001", "p ≤ 0.01". */
export function testPLabel(test: NormalityTest): string {
  const value = testP(test);
  return /^[<≤≥]/.test(value) ? `p ${value}` : `p = ${value}`;
}

/** "p = 0.034" or "p < 0.001". */
export function pLabel(p: number | null): string {
  const value = formatP(p);
  return value.startsWith("<") ? `p ${value}` : `p = ${value}`;
}

/** One or two sentences: how many tests reject, and how to read that for large samples. */
export function normalitySummary(normality: Normality, alpha: number): string[] {
  if (normality.reason) return [t("normality.none", { reason: normality.reason })];
  const ran = normality.tests.filter((test) => test.p_value !== null);
  const rejected = ran.filter((test) => rejects(test, alpha)).length;
  const sentences = [
    rejected
      ? t("normality.summary", { rejected: String(rejected), total: String(ran.length), alpha: String(alpha) })
      : t("normality.summaryNone", { alpha: String(alpha) }),
  ];
  if (normality.n > LARGE_SAMPLE && rejected) sentences.push(t("normality.large", { n: formatCount(normality.n) }));
  return sentences;
}

/** Overall verdict: normal when most tests that ran don't reject. */
export function isNormal(normality: Normality, alpha: number): boolean | null {
  const ran = normality.tests.filter((test) => test.p_value !== null);
  if (!ran.length) return null;
  const rejected = ran.filter((test) => rejects(test, alpha)).length;
  return rejected * 2 < ran.length;
}

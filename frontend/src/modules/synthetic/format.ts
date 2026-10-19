/** Numbers as the page writes them. */

export const pct = (value: number | null | undefined, digits = 0) =>
  value === null || value === undefined || Number.isNaN(value) ? "–" : `${(value * 100).toFixed(digits)} %`;

export function num(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "–";
  const size = Math.abs(value);
  if (size !== 0 && (size >= 1e6 || size < 1e-3)) return value.toExponential(2);
  return value.toLocaleString("en", { maximumFractionDigits: size >= 100 ? 1 : 3 });
}

/** "+4.2 %" for a signed share, "–" when there is none. */
export const signedPct = (value: number | null | undefined) =>
  value === null || value === undefined ? "–" : `${value >= 0 ? "+" : ""}${(value * 100).toFixed(1)} %`;

export const count = (value: number) => value.toLocaleString("en");

/** A score's tone: good from 85 %, weak under 50 % (the Quality thresholds of SDMetrics). */
export function tone(score: number | null | undefined): "good" | "fair" | "weak" | "none" {
  if (score === null || score === undefined) return "none";
  if (score >= 0.85) return "good";
  return score >= 0.5 ? "fair" : "weak";
}

export const toneText: Record<ReturnType<typeof tone>, string> = {
  good: "text-ink-1",
  fair: "text-warn",
  weak: "text-bad",
  none: "text-ink-3",
};

import type { Describe } from "../../api/client";
import { formatNumber } from "../../charts/figures";
import { formatCount } from "../../lib/format";
import { t, type MessageKey } from "../../lib/i18n";
import { InfoTip } from "../../ui/InfoTip";

export type StatKey = Exclude<keyof Describe, "distinct_approx">;
export type StatRow = { key: string; label: string; value: string; note?: string; explain?: string };

const COUNTS: StatKey[] = ["rows", "count", "missing", "infinite", "zeros", "negatives", "distinct"];
export const GROUPS: { title: MessageKey; keys: StatKey[] }[] = [
  { title: "variable.group.counts", keys: COUNTS },
  { title: "variable.group.center", keys: ["mean", "median", "std", "cv", "iqr", "mad", "sum"] },
  { title: "variable.group.quantiles", keys: ["min", "p1", "p5", "p10", "q1", "median", "q3", "p90", "p95", "p99", "max"] },
  { title: "variable.group.shape", keys: ["skewness", "kurtosis"] },
];

function share(part: number, whole: number): string | undefined {
  if (!whole || !part) return undefined;
  const value = (100 * part) / whole;
  return value < 0.1 ? "<0.1%" : `${value.toFixed(value < 10 ? 1 : 0)}%`;
}

/** A labelled, explained, formatted row for one statistic. */
export function statRow(summary: Describe, key: StatKey): StatRow {
  const value = summary[key];
  const isCount = COUNTS.includes(key);
  return {
    key,
    label: t(`vstat.${key}` as MessageKey),
    value: (key === "distinct" && summary.distinct_approx ? "≈ " : "") + (isCount ? formatCount(value) : formatNumber(value)),
    note: isCount && key !== "rows" && key !== "distinct" ? share(value ?? 0, summary.rows) : undefined,
    explain: t(`explain.${key}` as MessageKey),
  };
}

export function StatTable({ title, rows }: { title: string; rows: StatRow[] }) {
  return (
    <section className="min-w-0">
      <h3 className="mb-1.5 text-xs font-medium text-ink-3">{title}</h3>
      <dl className="divide-y divide-line rounded-md border border-line bg-surface-1">
        {rows.map((row) => (
          <div key={row.key} className="flex items-center justify-between gap-3 px-3 py-1.5">
            <dt className="flex min-w-0 items-center gap-1 text-ink-2">
              <span className="truncate">{row.label}</span>
              {row.explain && <InfoTip label={row.label} text={row.explain} />}
            </dt>
            <dd className="flex items-baseline gap-2 tabular-nums">
              {row.note && <span className="text-xs text-ink-3">{row.note}</span>}
              <span className="text-ink-1">{row.value}</span>
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

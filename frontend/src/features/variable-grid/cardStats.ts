import type { Chart, Column } from "../../api/client";
import { formatNumber } from "../../charts/figures";
import { formatCount } from "../../lib/format";
import { t } from "../../lib/i18n";

export type Stat = { label: string; value: string };

function pct(part: number, whole: number): string {
  if (!whole || !part) return "0%";
  const value = (100 * part) / whole;
  return value < 1 ? "<1%" : `${Math.round(value)}%`;
}

/** The two or three numbers worth reading under a card's chart. */
export function cardStats(column: Column, chart: Chart | undefined): Stat[] {
  const missing = { label: t("stat.missing"), value: pct(chart?.missing ?? 0, chart?.rows ?? 0) };
  if (!chart) return [];
  if (chart.kind === "histogram" && chart.stats && chart.view !== "lengths") {
    return [
      { label: t("stat.mean"), value: formatNumber(chart.stats.mean) },
      { label: t("stat.median"), value: formatNumber(chart.stats.median) },
      { label: t("stat.std"), value: formatNumber(chart.stats.std) },
      missing,
    ];
  }
  if (chart.view === "lengths" && chart.stats) {
    return [{ label: t("stat.avgLength"), value: formatNumber(chart.stats.mean) }, missing];
  }
  if (chart.kind === "timeline") {
    const first = chart.bars[0]?.label ?? "—";
    const last = chart.bars.at(-1)?.label ?? "—";
    return [{ label: t("stat.range"), value: `${first} → ${last}` }, missing];
  }
  if (chart.kind === "bars") {
    const top = column.type === "categorical_ordinal" || column.type === "numeric_discrete"
      ? undefined
      : chart.bars[0];
    const present = chart.rows - chart.missing;
    return [
      { label: t("stat.distinct"), value: formatCount(chart.distinct) },
      ...(top ? [{ label: top.label, value: pct(top.count, present) }] : []),
      missing,
    ];
  }
  return [missing];
}

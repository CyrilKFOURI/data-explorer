import { ArrowDownRight, ArrowRight, ArrowUpRight } from "lucide-react";

import type { KpiResult } from "../../api/client";
import { t } from "../../lib/i18n";
import type { Format } from "./definition";
import { formatChange, formatShare, formatValue } from "./format";

/** A mini line of the last periods, the tile's period marked. */
function Spark({ values, marked }: { values: (number | null)[]; marked: number | null }) {
  const points = values.map((v, i) => [i, v] as const).filter((p): p is readonly [number, number] => p[1] !== null);
  if (points.length < 2) return null;
  const low = Math.min(...points.map((p) => p[1]));
  const high = Math.max(...points.map((p) => p[1]));
  const x = (i: number) => (i / Math.max(1, values.length - 1)) * 116 + 2;
  const y = (v: number) => (high > low ? 26 - ((v - low) / (high - low)) * 22 : 15);
  const path = points.map(([i, v], k) => `${k ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const mark = marked !== null ? values[marked] : null;
  return (
    <svg viewBox="0 0 120 30" preserveAspectRatio="none" className="h-10 w-full min-w-24" aria-hidden>
      <path d={path} fill="none" stroke="var(--chart-1)" strokeWidth={1.5} strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
      {marked !== null && mark !== null && mark !== undefined && (
        <line x1={x(marked)} x2={x(marked)} y1={2} y2={28} stroke="var(--ink-3)" strokeDasharray="2 2" vectorEffect="non-scaling-stroke" />
      )}
    </svg>
  );
}

/** Up, down or flat, in neutral ink: a rise is not always good news (R-TILE-02). */
function Change({ change, against }: { change: number | null; against: string }) {
  if (change === null) return null;
  const Icon = change > 0.0005 ? ArrowUpRight : change < -0.0005 ? ArrowDownRight : ArrowRight;
  return (
    <span className="inline-flex items-center gap-0.5 text-xs text-ink-2">
      <Icon size={13} strokeWidth={1.75} aria-hidden />
      <span className="tabular-nums text-ink-1">{formatChange(change)}</span>
      <span className="text-ink-3">{against}</span>
    </span>
  );
}

export function Tiles({
  result,
  labels,
  formats,
}: {
  result: KpiResult;
  labels: Record<string, string>;
  formats: Record<string, Format>;
}) {
  return (
    <ul className="grid grid-cols-[repeat(auto-fit,minmax(240px,1fr))] border-y border-line" aria-label={t("kpi.tiles")}>
      {result.tiles.map((tile) => {
        const measure = result.measures.find((m) => m.id === tile.measure);
        if (!measure) return null;
        const custom = formats[tile.measure] ?? {};
        const value = formatValue(tile.value, measure.format, custom, "compact") || "—";
        return (
          <li key={tile.measure} className="border-line px-5 py-4 first:pl-0 [&:not(:first-child)]:border-l">
            <p className="truncate text-xs text-ink-2 first-letter:uppercase" title={labels[tile.measure]}>
              {labels[tile.measure]}
              {measure.approximate && <span title={t("kpi.approximate")}> ≈</span>}
            </p>
            <div className="mt-1 flex items-end gap-6">
              <div className="shrink-0">
                <p className="text-[32px] leading-tight font-semibold tracking-tight tabular-nums text-ink-1" title={formatValue(tile.value, measure.format, custom)}>
                  {value}
                </p>
                <p className="text-xs text-ink-3">{tile.period ?? t("kpi.tile.overall")}</p>
              </div>
              <div className="w-full max-w-72 min-w-24 pb-1">
                <Spark values={tile.spark} marked={tile.spark_index} />
              </div>
            </div>
            <div className="mt-2 flex flex-col gap-0.5">
              <Change
                change={tile.change}
                against={t("kpi.tile.vsPrevious", { value: formatValue(tile.previous, measure.format, custom, "compact") })}
              />
              <Change
                change={tile.change_yoy}
                against={t("kpi.tile.vsLastYear", { value: formatValue(tile.last_year, measure.format, custom, "compact") })}
              />
              {tile.top && (
                <span className="text-xs text-ink-2">
                  {t("kpi.tile.top", { label: tile.top.label, share: formatShare(tile.top.share) })}
                </span>
              )}
            </div>
          </li>
        );
      })}
    </ul>
  );
}

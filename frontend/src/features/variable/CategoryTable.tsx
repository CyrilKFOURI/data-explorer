import { useMemo, useState } from "react";

import type { Chart } from "../../api/client";
import { formatCount } from "../../lib/format";
import { t } from "../../lib/i18n";
import { TextInput } from "../../ui/fields";

/** Every category with its count, share and cumulative share; searchable. */
export function CategoryTable({ chart }: { chart: Chart }) {
  const [query, setQuery] = useState("");
  const present = chart.rows - chart.missing;
  const rows = useMemo(() => {
    const running = chart.bars.reduce<number[]>((sums, bar) => [...sums, (sums.at(-1) ?? 0) + bar.count], []);
    return chart.bars.map((bar, index) => ({
      ...bar,
      share: bar.count / (present || 1),
      cumulative: (running[index] ?? 0) / (present || 1),
    }));
  }, [chart.bars, present]);
  const needle = query.trim().toLowerCase();
  const visible = needle ? rows.filter((row) => row.label.toLowerCase().includes(needle)) : rows;
  const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

  return (
    <section>
      <div className="mb-2 flex items-center justify-between gap-3">
        <TextInput
          aria-label={t("fullscreen.search")}
          placeholder={t("fullscreen.search")}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          className="w-64"
        />
        <span className="text-xs text-ink-3">
          {t("fullscreen.count", { shown: formatCount(visible.length), total: formatCount(chart.distinct) })}
          {chart.missing > 0 && ` · ${t("fullscreen.missing", { count: formatCount(chart.missing) })}`}
        </span>
      </div>
      <div className="max-h-96 overflow-y-auto rounded-md border border-line">
        <table className="w-full border-collapse text-[13px]">
          <thead className="sticky top-0 bg-surface-2 text-left text-xs text-ink-3">
            <tr>
              <th scope="col" className="px-3 py-1.5 font-normal">{t("fullscreen.value")}</th>
              <th scope="col" className="px-3 py-1.5 text-right font-normal">{t("fullscreen.rows")}</th>
              <th scope="col" className="px-3 py-1.5 text-right font-normal">%</th>
              <th scope="col" className="px-3 py-1.5 text-right font-normal">{t("fullscreen.cumulative")}</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((row) => (
              <tr key={row.label} className="border-t border-line">
                <td className="max-w-0 truncate px-3 py-1" title={row.label}>{row.label}</td>
                <td className="px-3 py-1 text-right tabular-nums">{formatCount(row.count)}</td>
                <td className="px-3 py-1 text-right text-ink-2 tabular-nums">{pct(row.share)}</td>
                <td className="px-3 py-1 text-right text-ink-3 tabular-nums">{pct(row.cumulative)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

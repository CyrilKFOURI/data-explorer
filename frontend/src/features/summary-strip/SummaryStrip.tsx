import type { AnalysisType, Overview } from "../../api/client";
import { formatBytes, formatCount } from "../../lib/format";
import { t } from "../../lib/i18n";
import { ANALYSIS_TYPES, TYPE_META } from "../columns/columnTypes";

/** Dataset at a glance: size, completeness, duplicates, type mix. */
export function SummaryStrip({ overview }: { overview: Overview }) {
  const types = ANALYSIS_TYPES.filter((type) => overview.types[type]);
  const used = overview.used_columns;

  return (
    <section
      aria-label={t("summary.label")}
      className="grid grid-cols-2 gap-px overflow-hidden rounded-lg border border-line bg-line sm:grid-cols-3 lg:grid-cols-6"
    >
      <Tile label={t("summary.rows")} value={formatCount(overview.rows)} />
      <Tile
        label={t("summary.columns")}
        value={formatCount(used)}
        hint={used < overview.columns ? t("summary.excluded", { count: String(overview.columns - used) }) : undefined}
      />
      <Tile label={t("summary.missing")} value={`${overview.missing_pct}%`} hint={t("summary.cells", { count: formatCount(overview.missing_cells) })} />
      <Tile
        label={t("summary.duplicateRows")}
        value={formatCount(overview.duplicate_rows)}
        tone={overview.duplicate_rows ? "text-warn" : undefined}
      />
      <Tile
        label={t("summary.duplicateColumns")}
        value={formatCount(overview.duplicate_columns.reduce((sum, group) => sum + group.length - 1, 0))}
        tone={overview.duplicate_columns.length ? "text-warn" : undefined}
      />
      <Tile
        label={t("summary.size")}
        value={formatBytes(overview.size_bytes)}
        hint={overview.rows ? t("summary.perRow", { size: formatBytes(overview.size_bytes / overview.rows) }) : undefined}
      />
      <div className="col-span-full bg-surface-1 px-4 py-2.5">
        <div className="flex h-2 gap-[2px] overflow-hidden rounded-full" aria-hidden>
          {types.map((type) => (
            <span
              key={type}
              className={`h-full ${TYPE_META[type].swatch}`}
              style={{ width: `${((overview.types[type] ?? 0) / used) * 100}%` }}
            />
          ))}
        </div>
        <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-2">
          {types.map((type: AnalysisType) => {
            const meta = TYPE_META[type];
            const Icon = meta.icon;
            return (
              <li key={type} className="flex items-center gap-1.5">
                <Icon size={13} strokeWidth={1.5} className={meta.tone} aria-hidden />
                {t(meta.label)}
                <span className="text-ink-3 tabular-nums">{overview.types[type]}</span>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}

function Tile({ label, value, hint, tone }: { label: string; value: string; hint?: string; tone?: string }) {
  return (
    <div className="bg-surface-1 px-4 py-3">
      <p className="text-xs text-ink-3">{label}</p>
      <p className={`mt-0.5 text-lg font-semibold tabular-nums ${tone ?? "text-ink-1"}`}>{value}</p>
      {hint && <p className="text-[11px] text-ink-3">{hint}</p>}
    </div>
  );
}

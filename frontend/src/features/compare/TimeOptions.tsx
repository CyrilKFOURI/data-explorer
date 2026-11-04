import type { Comparison } from "../../api/client";
import { t, type MessageKey } from "../../lib/i18n";
import { Checkbox, Select } from "../../ui/fields";

export type Period = "hour" | "day" | "week" | "month" | "quarter" | "year";
export type Aggregate = "sum" | "mean" | "median" | "min" | "max" | "count";
export type Align = "trailing" | "centered";
export type Layer = "values" | "mean" | "band";

/** The time-series choices kept in the URL; undefined = automatic. */
export type TimeSearch = {
  period?: Period;
  agg?: Aggregate;
  window?: number;
  align?: Align;
  show?: string;
};

const PERIODS: Period[] = ["hour", "day", "week", "month", "quarter", "year"];
const AGGREGATES: Aggregate[] = [
  "sum",
  "mean",
  "median",
  "min",
  "max",
  "count",
];
const WINDOWS = [3, 4, 6, 7, 12, 14, 24, 26, 30, 52, 90];
const LAYERS: Layer[] = ["values", "mean", "band"];

const pick = <T extends string>(
  value: unknown,
  allowed: readonly T[],
): T | undefined =>
  typeof value === "string" && (allowed as readonly string[]).includes(value)
    ? (value as T)
    : undefined;

export function validateTimeSearch(
  search: Record<string, unknown>,
): TimeSearch {
  const window = Number(search.window);
  return {
    period: pick(search.period, PERIODS),
    agg: pick(search.agg, AGGREGATES),
    window:
      Number.isInteger(window) && window >= 2 && window <= 365
        ? window
        : undefined,
    align: pick(search.align, ["trailing", "centered"] as const),
    show: typeof search.show === "string" ? search.show : undefined,
  };
}

/** Layers drawn: every layer unless the URL lists some. */
export function shownLayers(show: string | undefined): Set<Layer> {
  if (show === undefined) return new Set(LAYERS);
  return new Set(
    show
      .split(",")
      .filter((layer): layer is Layer => (LAYERS as string[]).includes(layer)),
  );
}

/** "Weekly sum of revenue · 4-week rolling mean ± 1σ" */
export function timeSummary(result: Comparison): string {
  const time = result.time;
  if (!time) return "";
  const numeric = result.roles[result.x] === "date" ? result.y : result.x;
  const head = t("time.summary", {
    period: t(`time.periodly.${time.period}` as MessageKey),
    aggregate: t(`time.agg.${time.aggregate}` as MessageKey).toLowerCase(),
    column: numeric,
  });
  if (time.window === null) return head;
  const rolling = t(
    time.align === "centered" ? "time.rollingCentered" : "time.rolling",
    {
      window: String(time.window),
      period: t(`time.period.${time.period}` as MessageKey),
    },
  );
  return `${head} · ${rolling}`;
}

export function TimeOptions({
  result,
  search,
  onChange,
}: {
  result: Comparison;
  search: TimeSearch;
  onChange: (patch: TimeSearch) => void;
}) {
  const time = result.time;
  if (!time) return null;
  const layers = shownLayers(search.show);
  const toggle = (layer: Layer, on: boolean) => {
    const next = new Set(layers);
    if (on) next.add(layer);
    else next.delete(layer);
    onChange({
      show:
        next.size === LAYERS.length
          ? undefined
          : LAYERS.filter((l) => next.has(l)).join(","),
    });
  };
  const windows = WINDOWS.filter((w) => w <= Math.max(2, time.periods));

  return (
    <div
      className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-ink-2"
      role="group"
      aria-label={t("time.options")}
    >
      <label className="flex items-center gap-1.5">
        {t("time.period")}
        <Select
          value={search.period ?? ""}
          onChange={(event) =>
            onChange({
              period: (event.target.value || undefined) as Period | undefined,
            })
          }
          className="h-7 text-xs"
        >
          <option value="">
            {t("time.auto", {
              value: t(`time.periodName.${time.period}` as MessageKey),
            })}
          </option>
          {PERIODS.map((period) => (
            <option key={period} value={period}>
              {t(`time.periodName.${period}` as MessageKey)}
            </option>
          ))}
        </Select>
      </label>
      <label className="flex items-center gap-1.5">
        {t("time.aggregate")}
        <Select
          value={search.agg ?? ""}
          onChange={(event) =>
            onChange({
              agg: (event.target.value || undefined) as Aggregate | undefined,
            })
          }
          className="h-7 text-xs"
        >
          <option value="">
            {t("time.auto", {
              value: t(`time.agg.${time.aggregate}` as MessageKey),
            })}
          </option>
          {AGGREGATES.map((aggregate) => (
            <option key={aggregate} value={aggregate}>
              {t(`time.agg.${aggregate}` as MessageKey)}
            </option>
          ))}
        </Select>
      </label>
      {time.window !== null && (
        <>
          <label className="flex items-center gap-1.5">
            {t("time.window")}
            <Select
              value={search.window ? String(search.window) : ""}
              onChange={(event) =>
                onChange({
                  window: event.target.value
                    ? Number(event.target.value)
                    : undefined,
                })
              }
              className="h-7 text-xs"
            >
              <option value="">
                {t("time.auto", { value: String(time.window) })}
              </option>
              {windows.map((w) => (
                <option key={w} value={w}>
                  {w}
                </option>
              ))}
            </Select>
          </label>
          <Select
            aria-label={t("time.align")}
            value={time.align}
            onChange={(event) =>
              onChange({
                align:
                  event.target.value === "centered" ? "centered" : undefined,
              })
            }
            className="h-7 text-xs"
          >
            <option value="trailing">{t("time.align.trailing")}</option>
            <option value="centered">{t("time.align.centered")}</option>
          </Select>
          <span
            className="flex items-center gap-3"
            role="group"
            aria-label={t("time.show")}
          >
            {LAYERS.map((layer) => (
              <Checkbox
                key={layer}
                label={t(`time.layer.${layer}` as MessageKey)}
                checked={layers.has(layer)}
                disabled={layer === "band" && result.series.length > 1}
                title={
                  layer === "band" && result.series.length > 1
                    ? t("time.bandSingle")
                    : undefined
                }
                onChange={(event) => toggle(layer, event.target.checked)}
              />
            ))}
          </span>
        </>
      )}
    </div>
  );
}

/** Period, value, rolling mean, rolling σ and rows, for every series. */
export function TimeTable({ result }: { result: Comparison }) {
  const many = result.series.length > 1;
  const format = (value: number | null | undefined) =>
    value === null || value === undefined
      ? "—"
      : value.toLocaleString("en-US", { maximumSignificantDigits: 6 });
  return (
    <details className="mt-2 text-xs">
      <summary className="cursor-pointer text-ink-3 hover:text-ink-1">
        {t("time.table", { periods: String(result.time?.periods ?? 0) })}
      </summary>
      <div className="mt-2 max-h-72 overflow-auto rounded-md border border-line">
        <table className="w-full border-collapse tabular-nums">
          <thead className="sticky top-0 bg-surface-1 text-left text-ink-3">
            <tr>
              {many && (
                <th className="px-2 py-1 font-normal">
                  {t("time.col.series")}
                </th>
              )}
              <th className="px-2 py-1 font-normal">{t("time.col.period")}</th>
              <th className="px-2 py-1 text-right font-normal">
                {t("time.col.value")}
              </th>
              <th className="px-2 py-1 text-right font-normal">
                {t("time.col.mean")}
              </th>
              <th className="px-2 py-1 text-right font-normal">
                {t("time.col.std")}
              </th>
              <th className="px-2 py-1 text-right font-normal">
                {t("time.col.rows")}
              </th>
            </tr>
          </thead>
          <tbody>
            {result.series.flatMap((series) =>
              series.periods.map((period, i) => (
                <tr
                  key={`${series.label ?? ""}|${period}`}
                  className="border-t border-line"
                >
                  {many && <td className="px-2 py-0.5">{series.label}</td>}
                  <td className="px-2 py-0.5">{period}</td>
                  <td className="px-2 py-0.5 text-right">
                    {format(series.values[i])}
                  </td>
                  <td className="px-2 py-0.5 text-right">
                    {format(series.rolling_mean[i])}
                  </td>
                  <td className="px-2 py-0.5 text-right">
                    {format(series.rolling_std[i])}
                  </td>
                  <td className="px-2 py-0.5 text-right">
                    {series.counts[i] ?? 0}
                  </td>
                </tr>
              )),
            )}
          </tbody>
        </table>
      </div>
    </details>
  );
}

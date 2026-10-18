import type { SeriesParams } from "../../api/client";

export const PERIODS = [
  "hour",
  "day",
  "week",
  "month",
  "quarter",
  "year",
] as const;
export const AGGREGATES = [
  "sum",
  "mean",
  "median",
  "min",
  "max",
  "count",
] as const;
export const GAPS = ["leave", "interpolate", "zero", "carry"] as const;
export const DECOMPOSITIONS = [
  "stl",
  "mstl",
  "classical_additive",
  "classical_multiplicative",
] as const;
export type Decomposition = (typeof DECOMPOSITIONS)[number];
export const TRANSFORMS = [
  "none",
  "log",
  "diff",
  "seasonal_diff",
  "log_diff",
  "diff2",
  "seasonal_diff_diff",
] as const;
export type Transform = (typeof TRANSFORMS)[number];
export const PACF = ["ywm", "ols", "burg"] as const;

/** URL of the Time series page: the series parameters, plus display choices. */
export type TimeSeriesSearch = SeriesParams & {
  method?: Decomposition;
  transform?: Transform; // stationarity and autocorrelation sections
  pacf?: (typeof PACF)[number];
  rsource?: "series" | "returns"; // residuals section (default: residuals)
  segment?: "binseg"; // change-point search (default: PELT)
  cost?: "mean" | "mean_var" | "trend"; // default: chosen from the data
  sens?: "low" | "high";
  anomaly?: "iqr" | "rolling_z" | "hampel";
  threshold?: number;
  all?: boolean; // overlay every group on the overview
};

const text = (value: unknown) =>
  typeof value === "string" && value ? value : undefined;
const oneOf = <T extends string>(
  value: unknown,
  allowed: readonly T[],
): T | undefined =>
  typeof value === "string" && (allowed as readonly string[]).includes(value)
    ? (value as T)
    : undefined;
const integer = (value: unknown, low: number, high: number) => {
  const number = Number(value);
  return Number.isInteger(number) && number >= low && number <= high
    ? number
    : undefined;
};

export function validateTimeSeriesSearch(
  search: Record<string, unknown>,
): TimeSeriesSearch {
  return {
    time: text(search.time),
    value: text(search.value),
    group: text(search.group),
    series: text(search.series),
    period: oneOf(search.period, PERIODS),
    agg: oneOf(search.agg, AGGREGATES),
    window: integer(search.window, 2, 365),
    align: oneOf(search.align, ["trailing", "centered"] as const),
    gaps: oneOf(search.gaps, GAPS),
    season: integer(search.season, 2, 400),
    method: oneOf(search.method, DECOMPOSITIONS),
    transform: oneOf(search.transform, TRANSFORMS),
    pacf: oneOf(search.pacf, PACF),
    rsource: oneOf(search.rsource, ["series", "returns"] as const),
    segment: oneOf(search.segment, ["binseg"] as const),
    cost: oneOf(search.cost, ["mean", "mean_var", "trend"] as const),
    sens: oneOf(search.sens, ["low", "high"] as const),
    anomaly: oneOf(search.anomaly, ["iqr", "rolling_z", "hampel"] as const),
    threshold: [3, 4].includes(Number(search.threshold))
      ? Number(search.threshold)
      : undefined,
    all: search.all === true || search.all === "true" ? true : undefined,
  };
}

/** The parameters sent to the API (display-only choices left out). */
export function seriesParams(search: TimeSeriesSearch): SeriesParams {
  const params: TimeSeriesSearch = { ...search };
  delete params.method;
  delete params.transform;
  delete params.pacf;
  for (const key of [
    "rsource",
    "segment",
    "cost",
    "sens",
    "anomaly",
    "threshold",
  ] as const)
    delete params[key];
  delete params.all;
  return params;
}

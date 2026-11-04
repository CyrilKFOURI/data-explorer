import type { KpiNumberFormat } from "../../api/client";
import type { Format, ShowAs } from "./definition";

export type Mode = "full" | "compact";

/** Values shown as shares or relative changes are percentages, whatever the measure. */
export const PERCENT_MODES = new Set<ShowAs>(["share_total", "share_row", "share_column", "change_pct", "change_yoy"]);
const SIGNED_MODES = new Set<ShowAs>(["change", "change_pct", "change_yoy"]);

const MINUS = "−";

function digits(value: number, decimals: number): string {
  return value.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

function compact(value: number): string {
  return new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(value);
}

/** A measure's value with its automatic format (from the server) and the user's overrides:
 *  tiles and axes are compact (12.3K), the table shows full numbers (spec 022, section 7). */
export function formatValue(
  value: number | null | undefined,
  auto: KpiNumberFormat,
  custom: Format = {},
  mode: Mode = "full",
  signed = false,
): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "";
  const scaled = value * auto.scale;
  const decimals = typeof custom.decimals === "number" ? custom.decimals : auto.decimals;
  const short = custom.compact === "on" || (custom.compact !== "off" && mode === "compact" && Math.abs(scaled) >= 10_000);
  const body = short ? compact(Math.abs(scaled)) : digits(Math.abs(scaled), decimals);
  const sign = scaled < 0 ? MINUS : signed && scaled > 0 ? "+" : "";
  const prefix = custom.prefix || auto.prefix;
  const suffix = custom.suffix || auto.suffix;
  return `${sign}${prefix}${body}${suffix}`;
}

/** A relative change (0.042) as "+4.2 %". */
export function formatChange(change: number | null | undefined): string {
  if (change === null || change === undefined || !Number.isFinite(change)) return "";
  const percent = change * 100;
  const sign = percent < 0 ? MINUS : percent > 0 ? "+" : "";
  return `${sign}${digits(Math.abs(percent), Math.abs(percent) < 10 ? 1 : 0)} %`;
}

/** A share (0.34) as "34.0 %". */
export function formatShare(share: number | null | undefined): string {
  if (share === null || share === undefined || !Number.isFinite(share)) return "";
  return `${digits(share * 100, 1)} %`;
}

/** A value as the "Show as" setting presents it. */
export function formatShown(
  value: number | null | undefined,
  showAs: ShowAs,
  auto: KpiNumberFormat,
  custom: Format = {},
  mode: Mode = "full",
): string {
  if (showAs === "share_total" || showAs === "share_row" || showAs === "share_column") return formatShare(value);
  if (showAs === "change_pct" || showAs === "change_yoy") return formatChange(value);
  return formatValue(value, auto, custom, mode, SIGNED_MODES.has(showAs));
}

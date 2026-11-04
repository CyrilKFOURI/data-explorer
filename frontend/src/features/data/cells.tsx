import type { AnalysisType, Cell } from "../../api/client";
import { t } from "../../lib/i18n";

const number = new Intl.NumberFormat("en-US", { maximumFractionDigits: 6 });
const NUMERIC: AnalysisType[] = ["numeric_continuous", "numeric_discrete"];

/** Width in px from the type, widened for long names; text gets the most room. */
export function columnWidth(name: string, type: AnalysisType): number {
  const base: Record<AnalysisType, number> = {
    numeric_continuous: 128,
    numeric_discrete: 112,
    boolean: 96,
    datetime: 168,
    categorical_nominal: 152,
    categorical_ordinal: 152,
    identifier: 152,
    text: 240,
    ignored: 152,
  };
  // Room for the name plus the type icon, sort arrow, pin mark and menu button.
  return Math.min(Math.max(base[type], name.length * 7.5 + 96), 340);
}

export const isRightAligned = (type: AnalysisType) => NUMERIC.includes(type);

/** ISO timestamps without a time part read as plain dates. */
function formatDate(value: string): string {
  const [day, time] = value.split("T");
  if (!time || /^00:00(:00(\.0+)?)?$/.test(time)) return day ?? value;
  return `${day} ${time.replace(/(\.\d+)?$/, "").replace(/:00$/, "")}`;
}

export function formatCell(value: Cell, type: AnalysisType): string {
  if (value === null || typeof value === "object") return "";
  if (typeof value === "number") return NUMERIC.includes(type) || type === "ignored" ? number.format(value) : String(value);
  if (typeof value === "boolean") return value ? "true" : "false";
  return type === "datetime" ? formatDate(value) : value;
}

export function CellView({ value, type }: { value: Cell; type: AnalysisType }) {
  if (value === null) {
    return (
      <span className="text-ink-3" aria-label={t("data.missing")}>
        —
      </span>
    );
  }
  if (typeof value === "object") {
    return (
      <span className="text-warn italic" title={t("data.invalid", { value: value.invalid })}>
        {value.invalid}
      </span>
    );
  }
  const text = formatCell(value, type);
  return <span title={text.length > 24 ? text : undefined}>{text}</span>;
}

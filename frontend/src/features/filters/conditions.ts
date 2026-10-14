import type { AnalysisType } from "../../api/client";
import type { Condition } from "../../api/filters";

/** What the user picks in the editor: an operator plus "is not". */
export type Choice = {
  id: string;
  label: string;
  op: Condition["op"];
  negate: boolean;
  /** Which inputs the choice needs. */
  input: "none" | "value" | "range" | "values" | "part" | "rows";
};

const NUMBER: Choice[] = [
  { id: "eq", label: "=", op: "eq", negate: false, input: "value" },
  { id: "neq", label: "≠", op: "eq", negate: true, input: "value" },
  { id: "gt", label: ">", op: "gt", negate: false, input: "value" },
  { id: "gte", label: "≥", op: "gte", negate: false, input: "value" },
  { id: "lt", label: "<", op: "lt", negate: false, input: "value" },
  { id: "lte", label: "≤", op: "lte", negate: false, input: "value" },
  { id: "between", label: "between", op: "between", negate: false, input: "range" },
  { id: "outside", label: "outside", op: "between", negate: true, input: "range" },
];
const VALUES: Choice[] = [
  { id: "in", label: "is any of", op: "in", negate: false, input: "values" },
  { id: "not_in", label: "is none of", op: "in", negate: true, input: "values" },
];
const TEXT: Choice[] = [
  { id: "contains", label: "contains", op: "contains", negate: false, input: "value" },
  { id: "not_contains", label: "doesn't contain", op: "contains", negate: true, input: "value" },
  { id: "starts_with", label: "starts with", op: "starts_with", negate: false, input: "value" },
  { id: "eq", label: "equals", op: "eq", negate: false, input: "value" },
];
const DATE: Choice[] = [
  { id: "lt", label: "before", op: "lt", negate: false, input: "value" },
  { id: "gt", label: "after", op: "gt", negate: false, input: "value" },
  { id: "between", label: "between", op: "between", negate: false, input: "range" },
  { id: "outside", label: "outside", op: "between", negate: true, input: "range" },
  { id: "part_in", label: "falls on", op: "part_in", negate: false, input: "part" },
  { id: "part_not_in", label: "doesn't fall on", op: "part_in", negate: true, input: "part" },
];
const EMPTY: Choice[] = [
  { id: "is_null", label: "is empty", op: "is_null", negate: false, input: "none" },
  { id: "not_null", label: "is not empty", op: "is_null", negate: true, input: "none" },
];

/** Act on rows as a whole: one row per value, or the repeated values only (any column type). */
const ROWS: Choice[] = [
  { id: "unique", label: "unique values (one row each)", op: "unique", negate: false, input: "rows" },
  { id: "duplicated", label: "duplicates only", op: "duplicated", negate: false, input: "rows" },
  { id: "not_duplicated", label: "values appearing once", op: "duplicated", negate: true, input: "rows" },
];

export function choicesFor(type: AnalysisType): Choice[] {
  if (type === "numeric_continuous") return [...NUMBER, ...EMPTY, ...ROWS];
  if (type === "numeric_discrete") return [...VALUES, ...NUMBER, ...EMPTY, ...ROWS];
  if (type === "categorical_nominal" || type === "categorical_ordinal") return [...VALUES, ...TEXT, ...EMPTY, ...ROWS];
  if (type === "boolean") return [...VALUES, ...EMPTY, ...ROWS];
  if (type === "datetime") return [...DATE, ...EMPTY, ...ROWS];
  if (type === "text" || type === "identifier") return [...TEXT, ...VALUES, ...EMPTY, ...ROWS];
  return [];
}

export function choiceOf(condition: Condition, type: AnalysisType): Choice | undefined {
  return choicesFor(type).find((choice) => choice.op === condition.op && choice.negate === condition.negate);
}

/** Date parts offered by "falls on", with their values as the SQL part returns them. */
export const PARTS: Record<string, { label: string; values: { value: string; label: string }[] }> = {
  day_of_week: {
    label: "Day of week",
    values: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((label, i) => ({ value: String(i + 1), label })),
  },
  month: {
    label: "Month",
    values: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"].map((label, i) => ({
      value: String(i + 1),
      label,
    })),
  },
  quarter: { label: "Quarter", values: [1, 2, 3, 4].map((q) => ({ value: String(q), label: `Q${q}` })) },
  hour: { label: "Hour", values: Array.from({ length: 24 }, (_, h) => ({ value: String(h), label: `${h}h` })) },
};

const SYMBOLS: Partial<Record<Condition["op"], [string, string]>> = {
  eq: ["=", "≠"],
  gt: [">", "≤"],
  gte: ["≥", "<"],
  lt: ["<", "≥"],
  lte: ["≤", ">"],
};

function list(values: string[], max = 3): string {
  const shown = values.slice(0, max).join(", ");
  return values.length > max ? `${shown} +${values.length - max}` : shown;
}

function short(value: Condition["value"]): string {
  return typeof value === "string" && /^\d{4}-\d{2}-\d{2}T00:00/.test(value) ? value.slice(0, 10) : String(value ?? "");
}

/** "country ∈ FR, BE", "age ≥ 30", "signup_date on Mon", "vehicle_id · unique (last by date)"... */
export function describe(condition: Condition): string {
  const { column, op, negate } = condition;
  if (op === "unique" || op === "duplicated") {
    const key = [column, ...(condition.columns ?? [])].join(" + ");
    if (op === "duplicated") return `${key} · ${negate ? "appearing once" : "duplicates only"}`;
    const order = condition.order_by ? ` by ${condition.order_by}` : "";
    return `${key} · unique (${condition.keep ?? "first"}${order})`;
  }
  const symbols = SYMBOLS[op];
  if (symbols) return `${column} ${symbols[negate ? 1 : 0]} ${short(condition.value)}`;
  if (op === "between") {
    return `${column} ${negate ? "outside" : "in"} [${short(condition.low)} – ${short(condition.high)}]`;
  }
  if (op === "in") return `${column} ${negate ? "∉" : "∈"} ${list(condition.values ?? [])}`;
  if (op === "contains") return `${column} ${negate ? "doesn't contain" : "contains"} "${condition.value}"`;
  if (op === "starts_with") return `${column} starts with "${condition.value}"`;
  if (op === "is_null") return `${column} ${negate ? "is not empty" : "is empty"}`;
  const part = PARTS[condition.part ?? ""];
  const labels = (condition.values ?? []).map(
    (value) => part?.values.find((item) => item.value === value)?.label ?? value,
  );
  return `${column} ${negate ? "not on" : "on"} ${list(labels)}`;
}

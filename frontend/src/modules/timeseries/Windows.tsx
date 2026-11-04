import { Plus, X } from "lucide-react";
import { useState } from "react";

import { t } from "../../lib/i18n";
import { TextInput } from "../../ui/fields";

export const MAX_WINDOWS = 5;

/** "7,15" → [7, 15]: whole numbers from 2 to 365, without repeats, five at most. */
export function parseWindows(text: string | undefined): number[] {
  if (!text) return [];
  const found: number[] = [];
  for (const part of text.split(",")) {
    const value = Number(part.trim());
    if (Number.isInteger(value) && value >= 2 && value <= 365 && !found.includes(value)) found.push(value);
  }
  return found.slice(0, MAX_WINDOWS);
}

/** Rolling mean and sample standard deviation, gaps skipped, half a window required —
 *  the same rule as the server (pandas' rolling with min_periods = ceil(window / 2)). */
export function rolling(
  values: (number | null)[],
  window: number,
  align: "trailing" | "centered",
): { mean: (number | null)[]; std: (number | null)[] } {
  const needed = Math.ceil(window / 2);
  const mean: (number | null)[] = [];
  const std: (number | null)[] = [];
  for (let i = 0; i < values.length; i++) {
    const start = align === "centered" ? i - Math.floor(window / 2) : i - window + 1;
    const chunk = values.slice(Math.max(0, start), Math.max(0, start + window)).filter((v): v is number => v !== null);
    if (chunk.length < needed) {
      mean.push(null);
      std.push(null);
      continue;
    }
    const average = chunk.reduce((a, b) => a + b, 0) / chunk.length;
    mean.push(average);
    std.push(chunk.length > 1 ? Math.sqrt(chunk.reduce((a, b) => a + (b - average) ** 2, 0) / (chunk.length - 1)) : null);
  }
  return { mean, std };
}

/** Free windows as removable chips; empty means automatic. */
export function WindowsPicker({
  label,
  windows,
  auto,
  maximum,
  multiple,
  onChange,
}: {
  label: string;
  windows: number[];
  auto: number | null;
  maximum: number;
  multiple: boolean;
  onChange: (windows: number[]) => void;
}) {
  const [draft, setDraft] = useState("");
  const value = Number(draft);
  const valid = Number.isInteger(value) && value >= 2 && value <= Math.min(365, maximum) && !windows.includes(value);
  const add = () => {
    if (!valid) return;
    onChange(multiple ? [...windows, value].slice(0, MAX_WINDOWS) : [value]);
    setDraft("");
  };
  return (
    <div className="flex flex-wrap items-center gap-1.5" role="group" aria-label={label}>
      <span>{label}</span>
      {windows.length === 0 && auto !== null && (
        <span className="rounded-full border border-dashed border-line px-2 py-0.5 text-ink-3">{t("time.auto", { value: String(auto) })}</span>
      )}
      {windows.map((w, i) => (
        <span key={w} className="inline-flex items-center gap-1 rounded-full border border-line bg-surface-1 py-0.5 pr-1 pl-2 text-ink-1">
          {w}
          {multiple && i === 0 && windows.length > 1 && <span className="text-ink-3">· {t("ts.windows.band")}</span>}
          <button
            type="button"
            aria-label={t("ts.windows.remove", { window: String(w) })}
            onClick={() => onChange(windows.filter((x) => x !== w))}
            className="rounded-full p-0.5 text-ink-3 hover:bg-surface-2 hover:text-ink-1"
          >
            <X size={11} strokeWidth={2} aria-hidden />
          </button>
        </span>
      ))}
      {(multiple ? windows.length < MAX_WINDOWS : true) && (
        <span className="inline-flex items-center gap-1">
          <TextInput
            type="number"
            min={2}
            max={Math.min(365, maximum)}
            value={draft}
            placeholder={multiple && windows.length ? t("ts.windows.another") : t("ts.windows.custom")}
            aria-label={t("ts.windows.input", { label })}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => event.key === "Enter" && add()}
            className="h-7 w-20 text-xs"
          />
          <button
            type="button"
            onClick={add}
            disabled={!valid}
            aria-label={t("ts.windows.add")}
            className="inline-flex size-7 items-center justify-center rounded-md text-accent hover:bg-accent-soft disabled:text-ink-3 disabled:hover:bg-transparent"
          >
            <Plus size={13} strokeWidth={2} aria-hidden />
          </button>
        </span>
      )}
    </div>
  );
}

import { Minus, Plus } from "lucide-react";
import { useRef, type KeyboardEvent, type PointerEvent } from "react";

import type { MlDistribution } from "../../api/client";
import { formatNumber } from "../../charts/figures";
import { t, type MessageKey } from "../../lib/i18n";
import { Button } from "../../ui/Button";
import { Checkbox, Select, TextInput } from "../../ui/fields";
import { InfoTip } from "../../ui/InfoTip";
import {
  defaultNames,
  edgesFor,
  MAX_CLASSES,
  MIN_CLASSES,
  smallClasses,
  unequal,
  type BinMethod,
  type Setup,
} from "./bins";

export type Cut = { edges: number[]; names: string[]; counts: number[] };

/** One shade of the accent per class, light to dark: the order shows. */
export function shade(index: number, count: number): string {
  const share = count <= 1 ? 100 : 25 + Math.round((75 * index) / (count - 1));
  return `color-mix(in oklab, var(--accent) ${share}%, var(--surface-1))`;
}

const METHODS: BinMethod[] = ["quantile", "width", "jenks", "custom"];

export function ClassesPanel({
  target,
  shape,
  setup,
  cut,
  onSetup,
}: {
  target: string;
  shape: MlDistribution;
  setup: Setup;
  cut: Cut;
  onSetup: (next: Setup) => void;
}) {
  const total = cut.counts.reduce((a, b) => a + b, 0);
  const small = smallClasses(cut.counts);
  const wanted = setup.method === "values" ? cut.names.length : setup.k;
  const methods = shape.values && shape.values.length <= MAX_CLASSES ? [...METHODS, "values" as const] : METHODS;

  /** A structural change recomputes the limits, except in Custom where they stay the user's. */
  const change = (patch: Partial<Setup>) => {
    const next = { ...setup, ...patch };
    if (next.method === "custom") {
      const structural = patch.k !== undefined || patch.method !== undefined;
      next.edges = structural || !setup.edges ? edgesFor({ ...next, method: "quantile", edges: null }, shape) : setup.edges;
      if (patch.method === "custom") next.edges = cut.edges;
    } else if (patch.edges === undefined) {
      next.edges = null;
    }
    if (next.method === "values") next.k = shape.values?.length ?? next.k;
    onSetup(next);
  };
  const setEdge = (index: number, value: number) => {
    const edges = [...cut.edges];
    const low = index > 0 ? (edges[index - 1] as number) : (shape.min ?? -Infinity);
    const high = index < edges.length - 1 ? (edges[index + 1] as number) : (shape.max ?? Infinity);
    const span = ((shape.max ?? 1) - (shape.min ?? 0)) / 1000;
    edges[index] = Math.min(Math.max(value, low + span), high - span);
    onSetup({ ...setup, method: "custom", edges });
  };

  return (
    <div className="space-y-2.5 text-xs">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-ink-3">{t("ml.classes.count")}</span>
        <span className="inline-flex items-center gap-1">
          <Button
            variant="ghost"
            aria-label={t("ml.classes.fewer")}
            disabled={setup.method === "values" || setup.k <= MIN_CLASSES}
            onClick={() => change({ k: setup.k - 1 })}
          >
            <Minus size={14} strokeWidth={1.5} aria-hidden />
          </Button>
          <span className="w-5 text-center text-[13px] text-ink-1 tabular-nums" aria-live="polite">
            {cut.names.length}
          </span>
          <Button
            variant="ghost"
            aria-label={t("ml.classes.more")}
            disabled={setup.method === "values" || setup.k >= MAX_CLASSES}
            onClick={() => change({ k: setup.k + 1 })}
          >
            <Plus size={14} strokeWidth={1.5} aria-hidden />
          </Button>
        </span>
      </div>
      <label className="flex items-center justify-between gap-2">
        <span className="text-ink-3">{t("ml.classes.splitBy")}</span>
        <Select
          aria-label={t("ml.classes.splitBy")}
          value={setup.method}
          onChange={(event) => change({ method: event.target.value as BinMethod })}
          className="h-7 max-w-52 text-xs"
        >
          {methods.map((m) => (
            <option key={m} value={m}>
              {t(`ml.classes.method.${m}` as MessageKey, { target })}
            </option>
          ))}
        </Select>
      </label>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-ink-2">
        {setup.method !== "values" && setup.method !== "custom" && (
          <Checkbox label={t("ml.classes.round")} checked={setup.round} onChange={(e) => change({ round: e.target.checked })} />
        )}
        {setup.method === "width" && (
          <span className="inline-flex items-center gap-1">
            <Checkbox
              label={t("ml.classes.ignoreOutliers")}
              checked={setup.ignoreOutliers}
              onChange={(e) => change({ ignoreOutliers: e.target.checked })}
            />
            <InfoTip label={t("ml.classes.ignoreOutliers")} text={t("ml.classes.ignoreOutliersHint")} />
          </span>
        )}
      </div>
      <Histogram target={target} shape={shape} edges={cut.edges} draggable={setup.method === "custom"} onEdge={setEdge} />
      <ul className="space-y-1">
        {cut.names.map((name, i) => {
          const low = i > 0 ? cut.edges[i - 1] : undefined;
          const high = i < cut.edges.length ? cut.edges[i] : undefined;
          const count = cut.counts[i] ?? 0;
          const share = total ? count / total : 0;
          return (
            <li key={i} className="grid grid-cols-[10px_minmax(0,1fr)_auto] items-center gap-x-2">
              <span className="size-2.5 rounded-full" style={{ background: shade(i, cut.names.length) }} aria-hidden />
              <span className="flex min-w-0 items-center gap-2">
                <TextInput
                  aria-label={t("ml.classes.name", { index: String(i + 1) })}
                  value={setup.names[i] ?? name}
                  onChange={(event) => onSetup({ ...setup, names: { ...setup.names, [i]: event.target.value } })}
                  className="h-6 w-24 px-1 text-xs"
                />
                <span className="truncate text-ink-3 tabular-nums">
                  {low === undefined
                    ? t("ml.classes.upTo", { value: formatNumber(high) })
                    : high === undefined
                      ? t("ml.classes.above", { value: formatNumber(low) })
                      : t("ml.classes.between", { low: formatNumber(low), high: formatNumber(high) })}
                </span>
              </span>
              <span className="flex items-center gap-1.5 text-ink-2 tabular-nums">
                {count.toLocaleString("en-US")}
                <span className="w-8 text-right text-ink-3">{Math.round(share * 100)} %</span>
                <span className="h-1.5 w-12 overflow-hidden rounded-full bg-surface-2" aria-hidden>
                  <span className="block h-full rounded-full" style={{ width: `${share * 100}%`, background: shade(i, cut.names.length) }} />
                </span>
              </span>
            </li>
          );
        })}
      </ul>
      {small.map((i) => (
        <p key={i} className="flex flex-wrap items-center gap-2 text-warn" role="status">
          {t("ml.classes.small", { name: cut.names[i] ?? "", count: (cut.counts[i] ?? 0).toLocaleString("en-US") })}
          {setup.method !== "values" && cut.names.length > MIN_CLASSES ? (
            <Button variant="ghost" onClick={() => change({ k: cut.names.length - 1 })}>
              {t("ml.classes.useFewer", { count: String(cut.names.length - 1) })}
            </Button>
          ) : setup.method !== "quantile" && setup.method !== "values" ? (
            <Button variant="ghost" onClick={() => change({ method: "quantile" })}>
              {t("ml.classes.useEqualCounts")}
            </Button>
          ) : null}
        </p>
      ))}
      {cut.names.length < wanted && <p className="text-ink-2">{t("ml.classes.merged", { count: String(cut.names.length), wanted: String(wanted) })}</p>}
      {setup.method === "quantile" && unequal(cut.counts) && <p className="text-ink-2">{t("ml.classes.ties")}</p>}
      {!shape.values && <p className="text-ink-3">{t("ml.classes.estimated")}</p>}
    </div>
  );
}

function Histogram({
  target,
  shape,
  edges,
  draggable,
  onEdge,
}: {
  target: string;
  shape: MlDistribution;
  edges: number[];
  draggable: boolean;
  onEdge: (index: number, value: number) => void;
}) {
  const box = useRef<HTMLDivElement>(null);
  const low = shape.min ?? 0;
  const high = shape.max ?? 1;
  const span = high - low || 1;
  const peak = Math.max(1, ...shape.histogram);
  const x = (value: number) => ((value - low) / span) * 100;
  const valueAt = (clientX: number) => {
    const rect = box.current?.getBoundingClientRect();
    if (!rect || rect.width === 0) return low;
    return low + ((clientX - rect.left) / rect.width) * span;
  };
  const onKey = (index: number, value: number) => (event: KeyboardEvent) => {
    const step = (span / 100) * (event.shiftKey ? 10 : 1);
    if (event.key === "ArrowLeft" || event.key === "ArrowDown") onEdge(index, value - step);
    else if (event.key === "ArrowRight" || event.key === "ArrowUp") onEdge(index, value + step);
    else return;
    event.preventDefault();
  };
  const drag = (index: number) => (event: PointerEvent<HTMLDivElement>) => {
    if (event.buttons !== 1) return;
    onEdge(index, valueAt(event.clientX));
  };
  return (
    <div ref={box} className="relative h-[120px] w-full" role="img" aria-label={t("ml.classes.histogram", { target })}>
      <svg viewBox={`0 0 ${shape.histogram.length} 100`} preserveAspectRatio="none" className="absolute inset-0 h-full w-full" aria-hidden>
        {shape.histogram.map((count, i) => {
          const middle = low + ((i + 0.5) / shape.histogram.length) * span;
          const index = edges.filter((e) => middle > e).length;
          const h = (count / peak) * 96;
          return <rect key={i} x={i + 0.1} width={0.8} y={100 - h} height={h} fill={shade(index, edges.length + 1)} />;
        })}
      </svg>
      {edges.map((edge, i) => (
        <div
          key={i}
          className={`absolute top-0 bottom-0 -ml-px w-0.5 bg-ink-1 ${draggable ? "cursor-ew-resize" : ""}`}
          style={{ left: `${x(edge)}%` }}
        >
          {draggable && (
            <div
              role="slider"
              tabIndex={0}
              aria-label={t("ml.classes.limit", { index: String(i + 1) })}
              aria-valuemin={low}
              aria-valuemax={high}
              aria-valuenow={edge}
              aria-valuetext={formatNumber(edge)}
              onKeyDown={onKey(i, edge)}
              onPointerDown={(event) => event.currentTarget.setPointerCapture(event.pointerId)}
              onPointerMove={drag(i)}
              className="absolute -top-1 left-1/2 size-3.5 -translate-x-1/2 cursor-ew-resize rounded-full border-2 border-surface-1 bg-ink-1 outline-none focus-visible:ring-2 focus-visible:ring-accent"
            />
          )}
        </div>
      ))}
    </div>
  );
}

/** The setup that reproduces a saved run's classes exactly. */
export function setupFromRun(classes: { method: string; edges: number[]; names: string[] }): Setup {
  const defaults = defaultNames(classes.names.length);
  const names: Record<number, string> = {};
  classes.names.forEach((name, i) => {
    if (name !== defaults[i]) names[i] = name;
  });
  return {
    k: classes.names.length,
    method: classes.method as BinMethod,
    round: classes.method !== "custom",
    ignoreOutliers: true,
    names,
    edges: classes.edges,
  };
}

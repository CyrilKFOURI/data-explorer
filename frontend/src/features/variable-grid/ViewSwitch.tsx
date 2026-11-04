import type { Chart } from "../../api/client";
import { t, type MessageKey } from "../../lib/i18n";

const VIEW_LABELS: Record<string, MessageKey> = {
  histogram: "view.histogram",
  box: "view.box",
  bars: "view.bars",
  pie: "view.pie",
  timeline: "view.timeline",
  month: "view.month",
  day_of_week: "view.day_of_week",
  hour: "view.hour",
};

const STEP_LABELS: Record<string, MessageKey> = {
  hour: "step.hour",
  day: "step.day",
  week: "step.week",
  month: "step.month",
  quarter: "step.quarter",
  year: "step.year",
};

type ViewSwitchProps = {
  chart: Chart;
  onView: (view: string) => void;
  onStep?: (step: string) => void;
};

/** Tabs between the views of a chart (e.g. Timeline / Month / Day of week), plus the timeline step. */
export function ViewSwitch({ chart, onView, onStep }: ViewSwitchProps) {
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
      <div role="tablist" aria-label={t("view.label")} className="flex items-center gap-0.5">
        {chart.views.map((view) => {
          const active = view === chart.view;
          return (
            <button
              key={view}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => onView(view)}
              className={`rounded px-1.5 py-0.5 transition-colors ${
                active ? "bg-surface-2 font-medium text-ink-1" : "text-ink-3 hover:text-ink-1"
              }`}
            >
              {VIEW_LABELS[view] ? t(VIEW_LABELS[view]) : view}
            </button>
          );
        })}
      </div>
      {chart.kind === "timeline" && onStep && chart.steps.length > 1 && (
        <label className="ml-auto flex items-center gap-1 text-ink-3">
          {t("step.by")}
          <select
            value={chart.step ?? ""}
            onChange={(event) => onStep(event.target.value)}
            className="rounded border border-line bg-surface-1 px-1 py-0.5 text-ink-1"
          >
            {chart.steps.map((step) => (
              <option key={step} value={step}>
                {STEP_LABELS[step] ? t(STEP_LABELS[step]) : step}
              </option>
            ))}
          </select>
        </label>
      )}
    </div>
  );
}

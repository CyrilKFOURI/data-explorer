import { RotateCcw, X } from "lucide-react";
import type { ReactNode } from "react";

import type { KpiDefinition, KpiResult } from "../../api/client";
import { t, type MessageKey } from "../../lib/i18n";
import { Checkbox, Select, TextInput } from "../../ui/fields";
import { chartFor, chartName } from "./KpiCharts";
import {
  formatOf,
  RATIO,
  resetView,
  viewOf,
  withFormat,
  withLabel,
  withTable,
  withView,
  type ShowAs,
} from "./definition";
import { ADDITIVE_MODES, TIME_MODES } from "./pivot";

const SHOW_AS: ShowAs[] = ["value", "share_total", "share_row", "share_column", "change", "change_pct", "change_yoy", "running"];
const small = "h-8 w-full text-[13px]";

/** One setting: its control, what Auto chose (and why), and a reset link once changed. */
function Setting({
  label,
  auto,
  why,
  changed,
  onReset,
  children,
}: {
  label: string;
  auto?: string;
  why?: string | null;
  changed: boolean;
  onReset: () => void;
  children: ReactNode;
}) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-1.5 text-xs text-ink-2">
          {changed && <span className="size-1.5 rounded-full bg-accent" aria-label={t("kpi.customised")} />}
          {label}
        </span>
        {changed && (
          <button type="button" onClick={onReset} className="text-xs text-accent hover:underline">
            {t("kpi.resetAuto")}
          </button>
        )}
      </div>
      {children}
      {auto && !changed && (
        <p className="text-xs text-ink-3" title={why ?? undefined}>
          {auto}
        </p>
      )}
    </div>
  );
}

function Group({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="space-y-3 border-t border-line pt-3 first:border-0 first:pt-0">
      <h3 className="text-[13px] font-semibold text-ink-1">{title}</h3>
      {children}
    </section>
  );
}

export function Customize({
  definition,
  result,
  draft,
  onView,
  onData,
  onClose,
}: {
  definition: KpiDefinition; // applied: display changes are drawn at once
  result: KpiResult;
  draft: KpiDefinition; // what the builder holds: data changes wait for Calculate
  onView: (next: KpiDefinition) => void;
  onData: (next: KpiDefinition) => void;
  onClose: () => void;
}) {
  const view = viewOf(definition);
  const main = result.measures[0];
  const time = result.resolved.time;
  const grouped = result.splits.length > 0;
  const autoChart = main ? chartFor(main, "auto") : "none";
  const reasonFor = (mode: ShowAs): string | null => {
    if (TIME_MODES.has(mode) && !time) return t("kpi.reason.needsTime");
    if (ADDITIVE_MODES.has(mode) && main && !main.additive) return t("kpi.reason.notAdditive", { measure: main.label });
    if ((mode === "share_row" || mode === "share_column") && !grouped) return t("kpi.reason.needsSplit");
    return null;
  };
  const layoutOptions = result.resolved.layout.options;

  return (
    <aside className="space-y-4 border-line xl:border-l xl:pl-6" aria-label={t("kpi.customize")}>
      <div className="flex items-center justify-between">
        <h2 className="text-[15px] font-semibold text-ink-1">{t("kpi.customize")}</h2>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => onView(resetView(definition))}
            className="inline-flex h-7 items-center gap-1 rounded-md px-2 text-xs text-ink-2 hover:bg-surface-2 hover:text-ink-1"
          >
            <RotateCcw size={12} aria-hidden /> {t("kpi.resetAll")}
          </button>
          <button type="button" onClick={onClose} aria-label={t("kpi.close")} className="inline-flex size-7 items-center justify-center rounded-md text-ink-3 hover:bg-surface-2 hover:text-ink-1">
            <X size={14} aria-hidden />
          </button>
        </div>
      </div>

      <Group title={t("kpi.section.chart")}>
        {main && main.chart.options.length > 1 && (
          <Setting
            label={t("kpi.chartType")}
            auto={t("kpi.auto", { choice: chartName(autoChart) })}
            why={`${main.chart.rule} · ${main.chart.reason}`}
            changed={view.chart !== "auto"}
            onReset={() => onView(withView(definition, { chart: "auto" }))}
          >
            <div className="flex flex-wrap gap-1" role="radiogroup" aria-label={t("kpi.chartType")}>
              {main.chart.options.map((option) => {
                const selected = (view.chart === "auto" ? autoChart : view.chart) === option.value;
                return (
                  <button
                    key={option.value}
                    type="button"
                    role="radio"
                    aria-checked={selected}
                    disabled={!option.allowed}
                    title={option.reason ?? undefined}
                    onClick={() => onView(withView(definition, { chart: option.value === autoChart ? "auto" : (option.value as never) }))}
                    className={`rounded-md border px-2 py-1 text-xs ${selected ? "border-accent bg-accent-soft text-ink-1" : "border-line text-ink-2 hover:text-ink-1"} disabled:cursor-not-allowed disabled:border-dashed disabled:text-ink-3`}
                  >
                    {chartName(option.value)}
                  </button>
                );
              })}
            </div>
            {main.chart.options.filter((o) => !o.allowed).slice(0, 1).map((o) => (
              <p key={o.value} className="text-xs text-ink-3">
                {o.reason}
              </p>
            ))}
          </Setting>
        )}
        {main && time && grouped && (
          <Setting label={t("kpi.share")} changed={view.share} onReset={() => onView(withView(definition, { share: false }))}>
            <Checkbox
              label={t("kpi.shareLabel")}
              checked={view.share}
              disabled={!main.share.allowed}
              title={main.share.reason ?? undefined}
              onChange={(e) => onView(withView(definition, { share: e.target.checked }))}
              className="text-[13px]"
            />
            {!main.share.allowed && <p className="text-xs text-ink-3">{main.share.reason}</p>}
          </Setting>
        )}
        <Setting
          label={t("kpi.valueLabels")}
          auto={t("kpi.valueLabels.auto")}
          changed={view.labels !== "auto"}
          onReset={() => onView(withView(definition, { labels: "auto" }))}
        >
          <Select aria-label={t("kpi.valueLabels")} value={view.labels} onChange={(e) => onView(withView(definition, { labels: e.target.value as "auto" | "on" | "off" }))} className={small}>
            {(["auto", "on", "off"] as const).map((v) => (
              <option key={v} value={v}>
                {t(`kpi.switch.${v}` as MessageKey)}
              </option>
            ))}
          </Select>
        </Setting>
      </Group>

      <Group title={t("kpi.section.values")}>
        <Setting
          label={t("kpi.showAs")}
          auto={t("kpi.auto", { choice: t("kpi.showAs.value") })}
          changed={view.show_as !== "value"}
          onReset={() => onView(withView(definition, { show_as: "value" }))}
        >
          <Select aria-label={t("kpi.showAs")} value={view.show_as} onChange={(e) => onView(withView(definition, { show_as: e.target.value as ShowAs }))} className={small}>
            {SHOW_AS.map((mode) => {
              const reason = reasonFor(mode);
              return (
                <option key={mode} value={mode} disabled={Boolean(reason)} title={reason ?? undefined}>
                  {t(`kpi.showAs.${mode}` as MessageKey)}
                  {reason ? ` — ${reason}` : ""}
                </option>
              );
            })}
          </Select>
        </Setting>
      </Group>

      <Group title={t("kpi.section.table")}>
        {layoutOptions.length > 0 && (
          <Setting
            label={t("kpi.layout")}
            auto={t("kpi.auto", { choice: t(`kpi.layout.${result.resolved.layout.value}` as MessageKey) })}
            why={`${result.resolved.layout.rule} · ${result.resolved.layout.reason}`}
            changed={view.table.layout !== "auto"}
            onReset={() => onView(withTable(definition, { layout: "auto" }))}
          >
            <Select
              aria-label={t("kpi.layout")}
              value={view.table.layout}
              onChange={(e) => onView(withTable(definition, { layout: e.target.value as never }))}
              className={small}
            >
              <option value="auto">{t("kpi.autoPlain")}</option>
              {layoutOptions.map((o) => (
                <option key={o.value} value={o.value}>
                  {t(`kpi.layout.${o.value}` as MessageKey)}
                </option>
              ))}
            </Select>
          </Setting>
        )}
        <Setting label={t("kpi.totals")} auto={t("kpi.auto", { choice: t("kpi.switch.on") })} changed={view.table.totals !== "auto"} onReset={() => onView(withTable(definition, { totals: "auto" }))}>
          <Select aria-label={t("kpi.totals")} value={view.table.totals} onChange={(e) => onView(withTable(definition, { totals: e.target.value as "auto" | "on" | "off" }))} className={small}>
            {(["auto", "on", "off"] as const).map((v) => (
              <option key={v} value={v}>
                {t(`kpi.switch.${v}` as MessageKey)}
              </option>
            ))}
          </Select>
        </Setting>
        <Setting
          label={t("kpi.shading")}
          auto={t("kpi.auto", { choice: t(`kpi.switch.${result.resolved.shading.value}` as MessageKey) })}
          why={result.resolved.shading.reason}
          changed={view.table.shading !== "auto"}
          onReset={() => onView(withTable(definition, { shading: "auto" }))}
        >
          <Select aria-label={t("kpi.shading")} value={view.table.shading} onChange={(e) => onView(withTable(definition, { shading: e.target.value as "auto" | "on" | "off" }))} className={small}>
            {(["auto", "on", "off"] as const).map((v) => (
              <option key={v} value={v}>
                {t(`kpi.switch.${v}` as MessageKey)}
              </option>
            ))}
          </Select>
        </Setting>
        {time && (
          <Setting label={t("kpi.compare")} changed={view.table.compare.length > 0} onReset={() => onView(withTable(definition, { compare: [] }))}>
            <div className="flex flex-col gap-1 text-[13px]">
              {(["previous", "last_year"] as const).map((kind) => (
                <Checkbox
                  key={kind}
                  label={t(`kpi.compare.${kind}`)}
                  checked={view.table.compare.includes(kind)}
                  onChange={(e) =>
                    onView(withTable(definition, { compare: e.target.checked ? [...view.table.compare, kind] : view.table.compare.filter((k) => k !== kind) }))
                  }
                />
              ))}
            </div>
          </Setting>
        )}
      </Group>

      {grouped && (
        <Group title={t("kpi.section.groups")}>
          <Setting label={t("kpi.top")} auto={t("kpi.top.auto")} changed={(draft.top ?? 8) !== 8} onReset={() => onData({ ...draft, top: 8 })}>
            <TextInput
              type="number"
              min={1}
              max={20}
              aria-label={t("kpi.top")}
              value={draft.top ?? 8}
              onChange={(e) => onData({ ...draft, top: Math.min(20, Math.max(1, Number(e.target.value) || 1)) })}
              className={small}
            />
          </Setting>
          <Setting label={t("kpi.other")} changed={(definition.other ?? "show") !== "show"} onReset={() => onView({ ...definition, other: "show" })}>
            <Checkbox
              label={t("kpi.hideOther")}
              checked={definition.other === "hide"}
              onChange={(e) => onView({ ...definition, other: e.target.checked ? "hide" : "show" })}
              className="text-[13px]"
            />
          </Setting>
          <Setting label={t("kpi.order")} changed={(draft.group_order ?? "value") !== "value"} onReset={() => onData({ ...draft, group_order: "value" })}>
            <Select aria-label={t("kpi.order")} value={draft.group_order ?? "value"} onChange={(e) => onData({ ...draft, group_order: e.target.value as "value" | "alpha" })} className={small}>
              <option value="value">{t("kpi.order.value")}</option>
              <option value="alpha">{t("kpi.order.alpha")}</option>
            </Select>
          </Setting>
          <p className="text-xs text-ink-3">{t("kpi.groupsNeedCalculate")}</p>
        </Group>
      )}

      <Group title={t("kpi.section.format")}>
        {result.measures.map((measure) => {
          const custom = formatOf(definition, measure.id);
          const label = measure.id === RATIO ? definition.ratio?.label : definition.measures.find((m) => m.id === measure.id)?.label;
          const changed = Boolean(label) || (custom.decimals ?? "auto") !== "auto" || (custom.compact ?? "auto") !== "auto" || Boolean(custom.prefix || custom.suffix);
          return (
            <Setting
              key={measure.id}
              label={measure.label}
              auto={t("kpi.format.auto", { reason: measure.format.reason })}
              changed={changed}
              onReset={() => onView(withLabel(withFormat(definition, measure.id, { decimals: "auto", compact: "auto", prefix: "", suffix: "" }), measure.id, null))}
            >
              <div className="grid grid-cols-2 gap-1.5">
                <TextInput
                  aria-label={t("kpi.format.name")}
                  placeholder={t("kpi.format.name")}
                  value={label ?? ""}
                  maxLength={80}
                  onChange={(e) => onView(withLabel(definition, measure.id, e.target.value || null))}
                  className="col-span-2 h-8 text-[13px]"
                />
                <Select
                  aria-label={t("kpi.format.decimals")}
                  value={String(custom.decimals ?? "auto")}
                  onChange={(e) => onView(withFormat(definition, measure.id, { decimals: e.target.value === "auto" ? "auto" : Number(e.target.value) }))}
                  className="h-8 text-[13px]"
                >
                  <option value="auto">{t("kpi.format.decimalsAuto", { count: String(measure.format.decimals) })}</option>
                  {[0, 1, 2, 3, 4].map((d) => (
                    <option key={d} value={d}>
                      {t("kpi.format.decimalsN", { count: String(d) })}
                    </option>
                  ))}
                </Select>
                <Select
                  aria-label={t("kpi.format.compact")}
                  value={custom.compact ?? "auto"}
                  onChange={(e) => onView(withFormat(definition, measure.id, { compact: e.target.value as "auto" | "on" | "off" }))}
                  className="h-8 text-[13px]"
                >
                  <option value="auto">{t("kpi.format.compactAuto")}</option>
                  <option value="on">{t("kpi.format.compactOn")}</option>
                  <option value="off">{t("kpi.format.compactOff")}</option>
                </Select>
                <TextInput aria-label={t("kpi.format.prefix")} placeholder={t("kpi.format.prefix")} maxLength={8} value={custom.prefix ?? ""} onChange={(e) => onView(withFormat(definition, measure.id, { prefix: e.target.value }))} className="h-8 text-[13px]" />
                <TextInput aria-label={t("kpi.format.suffix")} placeholder={t("kpi.format.suffix")} maxLength={8} value={custom.suffix ?? ""} onChange={(e) => onView(withFormat(definition, measure.id, { suffix: e.target.value }))} className="h-8 text-[13px]" />
              </div>
            </Setting>
          );
        })}
      </Group>
    </aside>
  );
}

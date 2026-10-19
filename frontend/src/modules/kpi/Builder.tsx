import { Plus, Save, X } from "lucide-react";
import type { ReactNode } from "react";

import type { Column, KpiDefinition, KpiResult } from "../../api/client";
import { t, type MessageKey } from "../../lib/i18n";
import { Button } from "../../ui/Button";
import { Checkbox, Select, TextInput } from "../../ui/fields";
import {
  AGGS,
  columnsFor,
  dateColumns,
  defaultAgg,
  GRAINS,
  MAX_MEASURES,
  MAX_SPLITS,
  nextMeasureId,
  splitColumns,
  type Agg,
  type Measure,
} from "./definition";

type Period = NonNullable<NonNullable<KpiDefinition["time"]>["period"]>;
const PERIOD_KINDS: Period["kind"][] = ["all", "last", "ytd", "range"];

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-wrap items-center gap-2" role="group" aria-label={label}>
      <span className="w-20 shrink-0 text-xs text-ink-3">{label}</span>
      {children}
    </div>
  );
}

const small = "h-8 text-[13px]";
const iconButton =
  "inline-flex size-7 items-center justify-center rounded-md text-ink-3 hover:bg-surface-2 hover:text-ink-1";
const addButton =
  "inline-flex h-8 items-center gap-1 rounded-md px-2 text-[13px] text-accent hover:bg-accent-soft disabled:text-ink-3 disabled:hover:bg-transparent";

/** The KPI's four questions on one line each: what to measure, over which dates, split by what.
 *  A change here only takes effect with Calculate (spec 022, story 6). */
export function Builder({
  definition,
  columns,
  result,
  invalid,
  dirty,
  saving,
  saved,
  changed,
  onChange,
  onCalculate,
  onSave,
}: {
  definition: KpiDefinition;
  columns: Column[];
  result: KpiResult | undefined;
  invalid: string | null; // the field the server asked to fix
  dirty: boolean;
  saving: boolean;
  saved: boolean; // a saved KPI is open
  changed: boolean; // what is shown differs from what was saved
  onChange: (next: KpiDefinition) => void;
  onCalculate: () => void;
  onSave: () => void;
}) {
  const measures = definition.measures;
  const dates = dateColumns(columns);
  const splits = splitColumns(columns);
  const time = definition.time ?? null;
  const groups = definition.groups ?? [];
  const grain = result?.resolved.grain;
  const mark = (field: string) => (invalid === field ? "border-bad" : "");

  const setMeasure = (id: string, patch: Partial<Measure>) =>
    onChange({ ...definition, measures: measures.map((m) => (m.id === id ? { ...m, ...patch } : m)) });
  const setAgg = (measure: Measure, agg: Agg) => {
    const usable = columnsFor(agg, columns);
    const column = agg === "count" ? null : usable.some((c) => c.name === measure.column) ? measure.column : usable[0]?.name ?? null;
    setMeasure(measure.id, { agg, column });
  };
  const setColumn = (measure: Measure, name: string) => {
    const column = columns.find((c) => c.name === name);
    const agg = column && !columnsFor(measure.agg, columns).some((c) => c.name === name) ? defaultAgg(column) : measure.agg;
    setMeasure(measure.id, { column: name, agg });
  };
  const removeMeasure = (id: string) => {
    const ratio = definition.ratio && (definition.ratio.numerator === id || definition.ratio.denominator === id) ? null : definition.ratio;
    onChange({ ...definition, measures: measures.filter((m) => m.id !== id), ratio });
  };
  const setPeriod = (patch: Partial<Period>) =>
    time && onChange({ ...definition, time: { ...time, period: { ...(time.period ?? { kind: "all" }), ...patch } } });
  const period = time?.period ?? { kind: "all" as const };

  return (
    <section className="space-y-2.5 rounded-lg border border-line bg-surface-1 p-4" aria-label={t("kpi.builder")}>
      <Row label={t("kpi.measure")}>
        {measures.map((measure) => (
          <span key={measure.id} className="inline-flex items-center gap-1 rounded-md bg-surface-2 p-0.5 pr-1">
            <Select aria-label={t("kpi.aggregate")} value={measure.agg} onChange={(e) => setAgg(measure, e.target.value as Agg)} className={`${small} ${mark(`measures.${measure.id}.agg`)}`}>
              {AGGS.filter((agg) => agg === "count" || columnsFor(agg, columns).length > 0).map((agg) => (
                <option key={agg} value={agg}>
                  {t(`kpi.agg.${agg}` as MessageKey)}
                </option>
              ))}
            </Select>
            {measure.agg !== "count" && (
              <Select
                aria-label={t("kpi.column")}
                value={measure.column ?? ""}
                onChange={(e) => setColumn(measure, e.target.value)}
                className={`${small} max-w-44 ${mark(`measures.${measure.id}.column`)}`}
              >
                {!columnsFor(measure.agg, columns).some((c) => c.name === measure.column) && measure.column && (
                  <option value={measure.column}>{measure.column}</option>
                )}
                {columnsFor(measure.agg, columns).map((c) => (
                  <option key={c.name} value={c.name}>
                    {c.name}
                  </option>
                ))}
              </Select>
            )}
            {measures.length > 1 && (
              <button type="button" className={iconButton} aria-label={t("kpi.removeMeasure")} onClick={() => removeMeasure(measure.id)}>
                <X size={13} aria-hidden />
              </button>
            )}
          </span>
        ))}
        <button
          type="button"
          className={addButton}
          disabled={measures.length >= MAX_MEASURES}
          onClick={() => onChange({ ...definition, measures: [...measures, { id: nextMeasureId(measures), agg: "count" }] })}
        >
          <Plus size={13} aria-hidden /> {t("kpi.addMeasure")}
        </button>
        {!definition.ratio && (
          <button
            type="button"
            className={addButton}
            disabled={measures.length < 2}
            title={measures.length < 2 ? t("kpi.ratioNeedsTwo") : undefined}
            onClick={() => measures[0] && measures[1] && onChange({ ...definition, ratio: { numerator: measures[0].id, denominator: measures[1].id } })}
          >
            <Plus size={13} aria-hidden /> {t("kpi.addRatio")}
          </button>
        )}
      </Row>
      {definition.ratio && (
        <Row label={t("kpi.ratio")}>
          {(["numerator", "denominator"] as const).map((side, index) => (
            <span key={side} className="inline-flex items-center gap-2">
              {index === 1 && <span className="text-ink-3">÷</span>}
              <Select
                aria-label={t(`kpi.ratio.${side}`)}
                value={definition.ratio?.[side]}
                onChange={(e) => definition.ratio && onChange({ ...definition, ratio: { ...definition.ratio, [side]: e.target.value } })}
                className={small}
              >
                {measures.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.label || (m.agg === "count" ? t("kpi.agg.count") : `${t(`kpi.agg.${m.agg}` as MessageKey)} ${m.column}`)}
                  </option>
                ))}
              </Select>
            </span>
          ))}
          <Checkbox
            label={t("kpi.ratio.percent")}
            checked={Boolean(definition.ratio.percent)}
            onChange={(e) => definition.ratio && onChange({ ...definition, ratio: { ...definition.ratio, percent: e.target.checked } })}
            className="text-xs text-ink-2"
          />
          <button type="button" className={iconButton} aria-label={t("kpi.removeRatio")} onClick={() => onChange({ ...definition, ratio: null })}>
            <X size={13} aria-hidden />
          </button>
        </Row>
      )}
      <Row label={t("kpi.overTime")}>
        {dates.length === 0 ? (
          <span className="text-xs text-ink-3">{t("kpi.noDate")}</span>
        ) : (
          <>
            <Select
              aria-label={t("kpi.dateColumn")}
              value={time?.column ?? ""}
              onChange={(e) =>
                onChange({ ...definition, time: e.target.value ? { ...(time ?? {}), column: e.target.value } : null })
              }
              className={`${small} ${mark("time.column")}`}
            >
              <option value="">{t("kpi.noTime")}</option>
              {dates.map((c) => (
                <option key={c.name} value={c.name}>
                  {c.name}
                </option>
              ))}
            </Select>
            {time && (
              <>
                <Select
                  aria-label={t("kpi.grain")}
                  value={time.grain ?? "auto"}
                  onChange={(e) => onChange({ ...definition, time: { ...time, grain: e.target.value as typeof time.grain } })}
                  className={`${small} ${mark("time.grain")}`}
                  title={grain?.reason}
                >
                  <option value="auto">
                    {grain && (time.grain ?? "auto") === "auto" ? t("kpi.auto", { choice: t(`kpi.grain.${grain.value}` as MessageKey) }) : t("kpi.autoPlain")}
                  </option>
                  {GRAINS.map((g) => {
                    const option = grain?.options.find((o) => o.value === g);
                    return (
                      <option key={g} value={g} disabled={option ? !option.allowed : false} title={option?.reason ?? undefined}>
                        {t(`kpi.grain.${g}` as MessageKey)}
                      </option>
                    );
                  })}
                </Select>
                <span className="w-2" aria-hidden />
                <Select
                  aria-label={t("kpi.period")}
                  value={period.kind ?? "all"}
                  onChange={(e) => setPeriod({ kind: e.target.value as Period["kind"] })}
                  className={`${small} ${mark("time.period")}`}
                >
                  {PERIOD_KINDS.map((kind) => (
                    <option key={kind} value={kind}>
                      {t(`kpi.period.${kind}` as MessageKey)}
                    </option>
                  ))}
                </Select>
                {period.kind === "last" && (
                  <TextInput
                    type="number"
                    min={1}
                    max={2000}
                    aria-label={t("kpi.period.n")}
                    value={period.n ?? 12}
                    onChange={(e) => setPeriod({ n: Math.max(1, Number(e.target.value) || 1) })}
                    className={`${small} w-16`}
                  />
                )}
                {period.kind === "range" && (
                  <>
                    <TextInput type="date" aria-label={t("kpi.period.from")} value={period.from ?? ""} onChange={(e) => setPeriod({ from: e.target.value || null })} className={small} />
                    <span className="text-ink-3">→</span>
                    <TextInput type="date" aria-label={t("kpi.period.to")} value={period.to ?? ""} onChange={(e) => setPeriod({ to: e.target.value || null })} className={small} />
                  </>
                )}
                <Checkbox
                  label={t("kpi.pageFilters")}
                  checked={time.page_filters ?? true}
                  onChange={(e) => onChange({ ...definition, time: { ...time, page_filters: e.target.checked } })}
                  className="text-xs text-ink-2"
                />
              </>
            )}
          </>
        )}
      </Row>
      <Row label={t("kpi.splitBy")}>
        {groups.map((group, index) => (
          <span key={index} className="inline-flex items-center gap-1">
            {index > 0 && <span className="text-xs text-ink-3">{t("kpi.then")}</span>}
            <Select
              aria-label={t("kpi.splitColumn")}
              value={group.column}
              onChange={(e) => onChange({ ...definition, groups: groups.map((g, i) => (i === index ? { column: e.target.value } : g)) })}
              className={`${small} max-w-44 ${mark(`groups.${index}.column`)}`}
            >
              {splits
                .filter((c) => c.name === group.column || !groups.some((g) => g.column === c.name))
                .map((c) => (
                  <option key={c.name} value={c.name}>
                    {c.name}
                  </option>
                ))}
            </Select>
            <button type="button" className={iconButton} aria-label={t("kpi.removeSplit")} onClick={() => onChange({ ...definition, groups: groups.filter((_, i) => i !== index) })}>
              <X size={13} aria-hidden />
            </button>
          </span>
        ))}
        {groups.length < MAX_SPLITS && splits.some((c) => !groups.some((g) => g.column === c.name)) && (
          <button
            type="button"
            className={addButton}
            onClick={() => {
              const free = splits.find((c) => !groups.some((g) => g.column === c.name));
              if (free) onChange({ ...definition, groups: [...groups, { column: free.name }] });
            }}
          >
            <Plus size={13} aria-hidden /> {groups.length ? t("kpi.addSplit") : t("kpi.split")}
          </button>
        )}
        {groups.length === 0 && splits.length === 0 && <span className="text-xs text-ink-3">{t("kpi.noSplit")}</span>}
        <span className="ml-auto flex items-center gap-2">
          <Button variant="primary" onClick={onCalculate} disabled={!dirty}>
            {t("kpi.calculate")}
          </Button>
          <Button icon={Save} onClick={onSave} disabled={saving || (saved && !changed && !dirty)}>
            {saved ? t("kpi.saveChanges") : t("kpi.save")}
          </Button>
        </span>
      </Row>
    </section>
  );
}

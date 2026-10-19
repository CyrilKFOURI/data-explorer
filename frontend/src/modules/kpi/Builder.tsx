import { Plus, Save, X } from "lucide-react";
import type { ReactNode, SelectHTMLAttributes } from "react";

import type { Column, KpiDefinition, KpiResult } from "../../api/client";
import { t, type MessageKey } from "../../lib/i18n";
import { Button } from "../../ui/Button";
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

/** A choice inside the sentence: an underlined word that opens a native menu, as wide as its
 *  text. Red underline when the server asked to fix it. */
function Word({ invalid = false, className = "", ...props }: SelectHTMLAttributes<HTMLSelectElement> & { invalid?: boolean }) {
  return (
    <select
      {...props}
      className={`cursor-pointer appearance-none border-0 border-b-2 bg-transparent px-0.5 pb-0.5 font-semibold text-ink-1 outline-none [field-sizing:content] hover:border-accent focus-visible:border-accent ${invalid ? "border-bad" : "border-line"} ${className}`}
    />
  );
}

/** A small inline input in the sentence (a number of periods, a date). */
function Blank(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className="border-0 border-b-2 border-line bg-transparent px-0.5 pb-0.5 text-center font-semibold text-ink-1 outline-none [field-sizing:content] focus-visible:border-accent"
    />
  );
}

/** An addition inside the sentence: "+ measure", "+ split". */
function Add({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { children: ReactNode }) {
  return (
    <button
      type="button"
      {...props}
      className="inline-flex items-center gap-0.5 rounded px-1 text-[13px] text-accent hover:underline disabled:text-ink-3 disabled:no-underline"
    >
      <Plus size={12} aria-hidden />
      {children}
    </button>
  );
}

function Remove({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button type="button" aria-label={label} title={label} onClick={onClick} className="inline-flex size-5 items-center justify-center rounded text-ink-3 hover:text-ink-1">
      <X size={12} aria-hidden />
    </button>
  );
}

/** Connecting words of the sentence, in a quieter ink. */
const Glue = ({ children }: { children: ReactNode }) => <span className="text-ink-3">{children}</span>;

/** The KPI as a sentence: "Show Sum of revenue per month of date over all dates, split by
 *  country". Every underlined word is a choice. Changes take effect with Calculate. */
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
  const measureName = (m: Measure) =>
    m.label || (m.agg === "count" ? t("kpi.agg.count") : `${t(`kpi.aggShort.${m.agg}` as MessageKey).toLowerCase()} ${m.column}`);

  return (
    <section aria-label={t("kpi.builder")}>
      <div className="space-y-2.5 text-[17px] leading-9">
        <p className="flex flex-wrap items-baseline gap-x-1.5">
          <Glue>{t("kpi.s.show")}</Glue>
          {measures.map((measure, index) => (
            <span key={measure.id} className="inline-flex flex-wrap items-baseline gap-x-1.5">
              {index > 0 && <Glue>{index === measures.length - 1 ? t("kpi.s.and") : ","}</Glue>}
              <Word aria-label={t("kpi.aggregate")} value={measure.agg} onChange={(e) => setAgg(measure, e.target.value as Agg)} invalid={invalid === `measures.${measure.id}.agg`}>
                {AGGS.filter((agg) => agg === "count" || columnsFor(agg, columns).length > 0).map((agg) => (
                  <option key={agg} value={agg}>
                    {t(`kpi.aggShort.${agg}` as MessageKey)}
                  </option>
                ))}
              </Word>
              {measure.agg !== "count" && (
                <>
                  <Glue>{t("kpi.s.of")}</Glue>
                  <Word aria-label={t("kpi.column")} value={measure.column ?? ""} onChange={(e) => setColumn(measure, e.target.value)} invalid={invalid === `measures.${measure.id}.column`}>
                    {!columnsFor(measure.agg, columns).some((c) => c.name === measure.column) && measure.column && (
                      <option value={measure.column}>{measure.column}</option>
                    )}
                    {columnsFor(measure.agg, columns).map((c) => (
                      <option key={c.name} value={c.name}>
                        {c.name}
                      </option>
                    ))}
                  </Word>
                </>
              )}
              {measures.length > 1 && <Remove label={t("kpi.removeMeasure")} onClick={() => removeMeasure(measure.id)} />}
            </span>
          ))}
          {definition.ratio && (
            <span className="inline-flex flex-wrap items-baseline gap-x-1.5">
              <Glue>{t("kpi.s.ratio")}</Glue>
              {(["numerator", "denominator"] as const).map((side, index) => (
                <span key={side} className="contents">
                  {index === 1 && <Glue>÷</Glue>}
                  <Word
                    aria-label={t(`kpi.ratio.${side}`)}
                    value={definition.ratio?.[side]}
                    onChange={(e) => definition.ratio && onChange({ ...definition, ratio: { ...definition.ratio, [side]: e.target.value } })}
                  >
                    {measures.map((m) => (
                      <option key={m.id} value={m.id}>
                        {measureName(m)}
                      </option>
                    ))}
                  </Word>
                </span>
              ))}
              <label className="inline-flex items-center gap-1 text-[13px] text-ink-2">
                <input
                  type="checkbox"
                  className="size-3.5 accent-(--accent)"
                  checked={Boolean(definition.ratio.percent)}
                  onChange={(e) => definition.ratio && onChange({ ...definition, ratio: { ...definition.ratio, percent: e.target.checked } })}
                />
                {t("kpi.ratio.percent")}
              </label>
              <Remove label={t("kpi.removeRatio")} onClick={() => onChange({ ...definition, ratio: null })} />
            </span>
          )}
          <Add disabled={measures.length >= MAX_MEASURES} onClick={() => onChange({ ...definition, measures: [...measures, { id: nextMeasureId(measures), agg: "count" }] })}>
            {t("kpi.s.addMeasure")}
          </Add>
          {!definition.ratio && measures.length >= 2 && (
            <Add onClick={() => measures[0] && measures[1] && onChange({ ...definition, ratio: { numerator: measures[0].id, denominator: measures[1].id } })}>
              {t("kpi.s.addRatio")}
            </Add>
          )}
        </p>

        <p className="flex flex-wrap items-baseline gap-x-1.5">
          {dates.length === 0 || !time ? (
            <>
              <Glue>{t("kpi.s.overWhole")}</Glue>
              {dates.length > 0 && (
                <Add onClick={() => dates[0] && onChange({ ...definition, time: { column: dates[0].name } })}>{t("kpi.s.addTime")}</Add>
              )}
            </>
          ) : (
            <>
              <Glue>{t("kpi.s.per")}</Glue>
              <Word
                aria-label={t("kpi.grain")}
                value={time.grain ?? "auto"}
                title={grain?.reason}
                invalid={invalid === "time.grain"}
                onChange={(e) => onChange({ ...definition, time: { ...time, grain: e.target.value as typeof time.grain } })}
              >
                <option value="auto">
                  {grain && (time.grain ?? "auto") === "auto"
                    ? t("kpi.s.autoGrain", { grain: t(`kpi.grain.${grain.value}` as MessageKey).toLowerCase() })
                    : t("kpi.autoPlain")}
                </option>
                {GRAINS.map((g) => {
                  const option = grain?.options.find((o) => o.value === g);
                  return (
                    <option key={g} value={g} disabled={option ? !option.allowed : false} title={option?.reason ?? undefined}>
                      {t(`kpi.grain.${g}` as MessageKey).toLowerCase()}
                    </option>
                  );
                })}
              </Word>
              <Glue>{t("kpi.s.of")}</Glue>
              <Word
                aria-label={t("kpi.dateColumn")}
                value={time.column}
                invalid={invalid === "time.column"}
                onChange={(e) => onChange({ ...definition, time: e.target.value ? { ...time, column: e.target.value } : null })}
              >
                {dates.map((c) => (
                  <option key={c.name} value={c.name}>
                    {c.name}
                  </option>
                ))}
                <option value="">{t("kpi.s.noDate")}</option>
              </Word>
              <Glue>{t("kpi.s.over")}</Glue>
              <Word aria-label={t("kpi.period")} value={period.kind ?? "all"} invalid={invalid === "time.period"} onChange={(e) => setPeriod({ kind: e.target.value as Period["kind"] })}>
                {PERIOD_KINDS.map((kind) => (
                  <option key={kind} value={kind}>
                    {t(`kpi.s.period.${kind}` as MessageKey)}
                  </option>
                ))}
              </Word>
              {period.kind === "last" && (
                <>
                  <Blank type="number" min={1} max={2000} aria-label={t("kpi.period.n")} value={period.n ?? 12} onChange={(e) => setPeriod({ n: Math.max(1, Number(e.target.value) || 1) })} />
                  <Glue>{t("kpi.period.periods")}</Glue>
                </>
              )}
              {period.kind === "range" && (
                <>
                  <Glue>{t("kpi.s.from")}</Glue>
                  <Blank type="date" aria-label={t("kpi.period.from")} value={period.from ?? ""} onChange={(e) => setPeriod({ from: e.target.value || null })} />
                  <Glue>{t("kpi.s.to")}</Glue>
                  <Blank type="date" aria-label={t("kpi.period.to")} value={period.to ?? ""} onChange={(e) => setPeriod({ to: e.target.value || null })} />
                </>
              )}
              <label className="ml-2 inline-flex items-center gap-1 self-center text-[13px] text-ink-2" title={t("kpi.pageFilters.help")}>
                <input
                  type="checkbox"
                  className="size-3.5 accent-(--accent)"
                  checked={time.page_filters ?? true}
                  onChange={(e) => onChange({ ...definition, time: { ...time, page_filters: e.target.checked } })}
                />
                {t("kpi.pageFilters")}
              </label>
            </>
          )}
        </p>

        <p className="flex flex-wrap items-baseline gap-x-1.5">
          {groups.length > 0 && <Glue>{t("kpi.s.splitBy")}</Glue>}
          {groups.map((group, index) => (
            <span key={index} className="inline-flex items-baseline gap-x-1.5">
              {index > 0 && <Glue>{t("kpi.then")}</Glue>}
              <Word
                aria-label={t("kpi.splitColumn")}
                value={group.column}
                invalid={invalid === `groups.${index}.column`}
                onChange={(e) => onChange({ ...definition, groups: groups.map((g, i) => (i === index ? { column: e.target.value } : g)) })}
              >
                {splits
                  .filter((c) => c.name === group.column || !groups.some((g) => g.column === c.name))
                  .map((c) => (
                    <option key={c.name} value={c.name}>
                      {c.name}
                    </option>
                  ))}
              </Word>
              <Remove label={t("kpi.removeSplit")} onClick={() => onChange({ ...definition, groups: groups.filter((_, i) => i !== index) })} />
            </span>
          ))}
          {groups.length < MAX_SPLITS && splits.some((c) => !groups.some((g) => g.column === c.name)) && (
            <Add
              onClick={() => {
                const free = splits.find((c) => !groups.some((g) => g.column === c.name));
                if (free) onChange({ ...definition, groups: [...groups, { column: free.name }] });
              }}
            >
              {groups.length ? t("kpi.s.addSplitThen") : t("kpi.s.addSplit")}
            </Add>
          )}
        </p>
      </div>
      <div className="mt-2 flex flex-wrap items-center justify-end gap-3">
        <p className="mr-auto text-xs" aria-live="polite">
          {dirty ? <span className="text-ink-1">{t("kpi.pending")}</span> : <span className="text-ink-3">{t("kpi.upToDate")}</span>}
        </p>
        <Button variant="primary" onClick={onCalculate} disabled={!dirty}>
          {t("kpi.calculate")}
        </Button>
        <Button variant="ghost" icon={Save} onClick={onSave} disabled={saving || (saved && !changed && !dirty)}>
          {saved ? t("kpi.saveChanges") : t("kpi.save")}
        </Button>
      </div>
    </section>
  );
}

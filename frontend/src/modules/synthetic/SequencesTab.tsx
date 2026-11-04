import { useState } from "react";

import type { SyntheticPlan, SyntheticRequest, SyntheticRun } from "../../api/client";
import { Plot } from "../../charts/Plot";
import { t } from "../../lib/i18n";
import { Select, TextInput } from "../../ui/fields";
import { acfFigure, samplesFigure } from "./figures";
import { num, pct, tone, toneText } from "./format";

export type SequenceDraft = NonNullable<SyntheticRequest["sequence"]>;
type SequencePlan = NonNullable<SyntheticPlan["sequence"]>;

const small = "h-7 text-xs";

/** TimeGAN's settings in the bar: time, entity, length, how many sequences, training steps. */
export function SequenceSettings({
  plan,
  dates,
  draft,
  steps,
  onChange,
}: {
  plan: SequencePlan;
  dates: string[];
  draft: SequenceDraft;
  steps: number;
  onChange: (next: SequenceDraft) => void;
}) {
  const entity = draft.no_entity ? "" : (draft.entity ?? plan.entity ?? "");
  const entityChanged = draft.no_entity || (draft.entity !== undefined && draft.entity !== plan.entity);
  const length = draft.length ?? plan.length;
  const sequences = draft.sequences ?? (entityChanged ? null : plan.sequences);
  const number = (raw: string, low: number, high: number) =>
    raw === "" ? null : Math.min(high, Math.max(low, Math.round(Number(raw))));
  return (
    <div className="flex flex-wrap items-center gap-1.5" role="group" aria-label={t("synthetic.sequences")}>
      <span className="text-ink-3">{t("synthetic.time")}</span>
      <Select aria-label={t("synthetic.time")} value={draft.time ?? plan.time ?? ""} onChange={(e) => onChange({ ...draft, time: e.target.value })} className={`${small} max-w-32`}>
        {dates.map((d) => (
          <option key={d} value={d}>
            {d}
          </option>
        ))}
      </Select>
      <span className="text-ink-3">{t("synthetic.entity")}</span>
      <Select
        aria-label={t("synthetic.entity")}
        value={entity}
        onChange={(e) => onChange({ ...draft, entity: e.target.value || null, no_entity: e.target.value === "", sequences: null })}
        className={`${small} max-w-32`}
      >
        <option value="">{t("synthetic.oneSeries")}</option>
        {plan.candidates.map((c) => (
          <option key={c.name} value={c.name} title={c.reason}>
            {c.name}
          </option>
        ))}
      </Select>
      <span className="text-ink-3">{t("synthetic.length")}</span>
      <TextInput
        type="number"
        min={8}
        max={100}
        aria-label={t("synthetic.length")}
        value={draft.length ?? ""}
        placeholder={String(plan.length)}
        onChange={(e) => onChange({ ...draft, length: number(e.target.value, 8, 100) })}
        className={`${small} w-16 text-right`}
      />
      <span className="text-ink-3">{t("synthetic.sequenceCount")}</span>
      <TextInput
        type="number"
        min={1}
        max={10_000}
        aria-label={t("synthetic.sequenceCount")}
        value={draft.sequences ?? ""}
        placeholder={sequences === null ? t("synthetic.auto") : String(sequences)}
        onChange={(e) => onChange({ ...draft, sequences: number(e.target.value, 1, 10_000) })}
        className={`${small} w-20 text-right`}
      />
      <span className="text-ink-3">{t("synthetic.steps")}</span>
      <TextInput
        type="number"
        min={100}
        max={20_000}
        aria-label={t("synthetic.steps")}
        value={draft.steps ?? ""}
        placeholder={t("synthetic.epochsAuto", { epochs: String(steps) })}
        onChange={(e) => onChange({ ...draft, steps: number(e.target.value, 100, 20_000) })}
        className={`${small} w-28 text-right`}
      />
      {sequences !== null && (
        <span className="text-ink-3 tabular-nums">= {(sequences * length).toLocaleString("en")} {t("synthetic.rowsShort")}</span>
      )}
    </div>
  );
}

/** The paper's sequence measures, the autocorrelations and a few histories side by side. */
export function SequencesTab({ run }: { run: SyntheticRun }) {
  const report = run.report.sequences;
  const [column, setColumn] = useState(report?.samples[0]?.column ?? "");
  if (!report) return null;
  const sample = report.samples.find((s) => s.column === column) ?? report.samples[0];
  const figures = [
    { label: t("synthetic.autocorrelation"), value: report.autocorrelation, help: t("synthetic.autocorrelationHelp") },
    { label: t("synthetic.discriminative"), value: report.discriminative, help: t("synthetic.discriminativeHelp") },
    {
      label: t("synthetic.predictive"),
      value: report.predictive_ratio === null ? null : Math.min(report.predictive_ratio, 1),
      help: t("synthetic.predictiveHelp", { real: num(report.predictive_real), synthetic: num(report.predictive_synthetic) }),
    },
  ];
  return (
    <div className="space-y-6">
      <p className="text-xs text-ink-3">
        {t("synthetic.sequencesOf", {
          sequences: String(report.sequences),
          length: String(report.length),
          step: report.step,
          entity: report.entity ?? t("synthetic.oneSeries"),
          windows: report.train_windows.toLocaleString("en"),
        })}
      </p>
      <dl className="grid grid-cols-1 border-y border-line sm:grid-cols-3">
        {figures.map((f, i) => (
          <div key={f.label} className={`px-4 py-3 ${i > 0 ? "sm:border-l sm:border-line" : ""}`}>
            <dt className="text-xs text-ink-3">{f.label}</dt>
            <dd className={`text-[24px] leading-tight font-semibold tabular-nums ${toneText[tone(f.value)]}`}>{pct(f.value)}</dd>
            <dd className="text-xs text-ink-3">{f.help}</dd>
          </div>
        ))}
      </dl>
      <ul className="space-y-1 text-[13px] text-ink-2">
        {report.sentences.map((s) => (
          <li key={s}>{s}</li>
        ))}
      </ul>
      {report.columns.length > 0 && (
        <div className="grid gap-6 lg:grid-cols-2 xl:grid-cols-3">
          {report.columns.map((c) => (
            <figure key={c.column} className="space-y-1">
              <figcaption className="text-[13px] font-medium text-ink-1">
                {c.column} <span className="text-xs font-normal text-ink-3">{pct(c.similarity)}</span>
              </figcaption>
              <Plot figure={acfFigure(c)} height={200} label={t("synthetic.acfOf", { column: c.column })} />
            </figure>
          ))}
        </div>
      )}
      {sample && (
        <figure className="space-y-2">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <figcaption className="text-[13px] font-medium text-ink-1">{t("synthetic.sampleSequences")}</figcaption>
            <Select aria-label={t("synthetic.column")} value={sample.column} onChange={(e) => setColumn(e.target.value)} className={small}>
              {report.samples.map((s) => (
                <option key={s.column} value={s.column}>
                  {s.column}
                </option>
              ))}
            </Select>
          </div>
          <Plot figure={samplesFigure(sample)} height={280} label={t("synthetic.sampleSequences")} />
        </figure>
      )}
    </div>
  );
}

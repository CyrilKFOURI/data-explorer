import { Play } from "lucide-react";
import { useState } from "react";

import type { SyntheticRun } from "../../api/client";
import { useSyntheticActions } from "../../api/hooks";
import { Plot } from "../../charts/Plot";
import { t } from "../../lib/i18n";
import { Button } from "../../ui/Button";
import { Checkbox, ErrorNote, Select } from "../../ui/fields";
import { dcrFigure } from "./figures";
import { count, num, pct, tone, toneText } from "./format";
import { Table } from "./Report";

const cell = "py-1.5 pr-3 text-right";

/** Copies, memorisation, distances, rare values, and the optional disclosure risk (CAP). */
export function PrivacyTab({ run, datasetId }: { run: SyntheticRun; datasetId: string }) {
  const privacy = run.report.privacy;
  const actions = useSyntheticActions(datasetId);
  const learned = run.report.learned;
  const [known, setKnown] = useState<string[]>([]);
  const [sensitive, setSensitive] = useState(learned.find((l) => l.kind === "category")?.name ?? learned[0]?.name ?? "");
  const disclosure = actions.disclosure.data ?? run.report.disclosure;
  const measures: { label: string; value: string; score: number | null; reading: string }[] = [
    {
      label: t("synthetic.uniqueCopies"),
      value: `${count(privacy.unique_copies)} (${pct(privacy.unique_copy_share, 1)})`,
      score: 1 - privacy.unique_copy_share,
      reading: t("synthetic.uniqueCopiesHelp"),
    },
    {
      label: t("synthetic.exactCopies"),
      value: `${count(privacy.copies)} (${pct(privacy.copy_share, 1)})`,
      score: null,
      reading: t("synthetic.exactCopiesHelp"),
    },
    {
      label: t("synthetic.nearCopies"),
      value: `${count(privacy.near_copies)} · ${pct(privacy.new_rows, 1)}`,
      score: privacy.new_rows,
      reading: t("synthetic.nearCopiesHelp"),
    },
    {
      label: t("synthetic.overfitting"),
      value: pct(privacy.overfitting),
      score: privacy.overfitting,
      reading: t("synthetic.overfittingHelp", { share: pct(privacy.closer_to_train) }),
    },
    {
      label: t("synthetic.baseline"),
      value: pct(privacy.baseline),
      score: privacy.baseline,
      reading: t("synthetic.baselineHelp", { median: num(privacy.median_dcr) }),
    },
  ];
  return (
    <div className="space-y-8">
      <p className={`border-l-2 pl-3 text-[13px] ${privacy.warnings.length ? "border-bad text-bad" : "border-accent text-ink-1"}`}>{privacy.verdict}</p>
      <div className="grid gap-8 xl:grid-cols-2">
        <Table caption={t("synthetic.privacyMeasures")} head={[t("synthetic.measure"), t("synthetic.value"), t("synthetic.reading")]}>
          {measures.map((m) => (
            <tr key={m.label} className="border-b border-line/60 align-top">
              <td className="py-1.5 pr-3">{m.label}</td>
              <td className={`${cell} whitespace-nowrap ${toneText[tone(m.score)]}`}>{m.value}</td>
              <td className="py-1.5 pr-3 text-xs text-ink-3">{m.reading}</td>
            </tr>
          ))}
        </Table>
        {privacy.histogram && (
          <figure className="space-y-1">
            <figcaption className="text-[13px] font-medium text-ink-1">{t("synthetic.dcr")}</figcaption>
            <Plot figure={dcrFigure(privacy.histogram)} height={240} label={t("synthetic.dcr")} />
            <p className="text-xs text-ink-3">{t("synthetic.dcrHelp")}</p>
          </figure>
        )}
      </div>
      <div className="grid gap-8 xl:grid-cols-2">
        <div className="space-y-2">
          {privacy.rare.length === 0 ? (
            <>
              <h3 className="text-xs font-medium text-ink-2">{t("synthetic.rare")}</h3>
              <p className="text-[13px] text-ink-3">{t("synthetic.noRare")}</p>
            </>
          ) : (
            <Table caption={t("synthetic.rare")} head={[t("synthetic.column"), t("synthetic.value"), t("synthetic.realRows"), t("synthetic.syntheticRows")]}>
              {privacy.rare.map((r) => (
                <tr key={`${r.column}-${r.value}`} className="border-b border-line/60">
                  <td className="py-1.5 pr-3">{r.column}</td>
                  <td className={cell}>{r.value}</td>
                  <td className={cell}>{r.real}</td>
                  <td className={cell}>{r.synthetic}</td>
                </tr>
              ))}
            </Table>
          )}
          <p className="text-xs text-ink-3">{t("synthetic.rareHelp")}</p>
        </div>
        <div className="space-y-3">
          <h3 className="text-xs font-medium text-ink-2">{t("synthetic.cap")}</h3>
          <p className="text-xs text-ink-3">{t("synthetic.capHelp")}</p>
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-[13px]" role="group" aria-label={t("synthetic.known")}>
            <span className="w-full text-xs text-ink-3">{t("synthetic.known")}</span>
            {learned
              .filter((l) => l.name !== sensitive)
              .map((l) => (
                <Checkbox
                  key={l.name}
                  label={l.name}
                  checked={known.includes(l.name)}
                  onChange={(e) => setKnown(e.target.checked ? [...known, l.name].slice(-10) : known.filter((k) => k !== l.name))}
                />
              ))}
          </div>
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="text-ink-3">{t("synthetic.sensitive")}</span>
            <Select aria-label={t("synthetic.sensitive")} value={sensitive} onChange={(e) => setSensitive(e.target.value)} className="h-7 text-xs">
              {learned.map((l) => (
                <option key={l.name} value={l.name}>
                  {l.name}
                </option>
              ))}
            </Select>
            <Button
              icon={Play}
              disabled={known.length === 0 || actions.disclosure.isPending}
              onClick={() => actions.disclosure.mutate({ runId: run.id, known: known.filter((k) => k !== sensitive), sensitive })}
            >
              {t("synthetic.run")}
            </Button>
          </div>
          {actions.disclosure.error && <ErrorNote>{actions.disclosure.error.message}</ErrorNote>}
          {disclosure && (
            <Table
              caption={t("synthetic.capResult", { known: disclosure.known.join(", "), sensitive: disclosure.sensitive, baseline: pct(disclosure.baseline) })}
              head={[t("synthetic.variant"), t("synthetic.attack"), t("synthetic.protection")]}
            >
              {disclosure.variants.map((v) => (
                <tr key={v.name} className="border-b border-line/60">
                  <td className="py-1.5 pr-3">{v.name}</td>
                  <td className={cell}>{pct(v.attack)}</td>
                  <td className={`${cell} ${toneText[tone(v.protection)]}`}>{pct(v.protection)}</td>
                </tr>
              ))}
            </Table>
          )}
        </div>
      </div>
      <p className="text-xs text-ink-3">{t("synthetic.notDifferential")}</p>
    </div>
  );
}

/** Trained on synthetic vs on real, both tested on the same held-out real rows. */
export function UtilityTab({ run, datasetId }: { run: SyntheticRun; datasetId: string }) {
  const actions = useSyntheticActions(datasetId);
  const targets = run.report.learned.filter((l) => l.kind !== "date");
  const result = actions.utility.data ?? run.report.utility;
  const [target, setTarget] = useState(result?.target ?? targets[0]?.name ?? "");
  return (
    <div className="space-y-6">
      <p className="max-w-prose text-[13px] text-ink-2">{t("synthetic.utilityHelp")}</p>
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="text-ink-3">{t("synthetic.target")}</span>
        <Select aria-label={t("synthetic.target")} value={target} onChange={(e) => setTarget(e.target.value)} className="h-7 text-xs">
          {targets.map((l) => (
            <option key={l.name} value={l.name}>
              {l.name}
            </option>
          ))}
        </Select>
        <Button icon={Play} variant="primary" disabled={!target || actions.utility.isPending} onClick={() => actions.utility.mutate({ runId: run.id, target })}>
          {actions.utility.isPending ? t("synthetic.training") : t("synthetic.run")}
        </Button>
      </div>
      {actions.utility.error && <ErrorNote>{actions.utility.error.message}</ErrorNote>}
      {result && (
        <div className="space-y-4">
          <div className="border-y border-line py-3">
            <p className={`text-[28px] leading-tight font-semibold tabular-nums ${toneText[tone(result.ratio)]}`}>{pct(result.ratio)}</p>
            <p className="text-[13px] text-ink-2">{result.sentence}</p>
          </div>
          <Table
            caption={t("synthetic.utilityResult", { target: result.target, rows: count(result.test_rows) })}
            head={[t("synthetic.metric"), t("synthetic.trtr"), t("synthetic.tstr")]}
          >
            {result.metrics.map((m) => (
              <tr key={m.name} className="border-b border-line/60">
                <td className="py-1.5 pr-3">
                  {m.name}
                  {m.name === result.primary ? " ★" : ""}
                </td>
                <td className={cell}>{num(m.real)}</td>
                <td className={cell}>{num(m.synthetic)}</td>
              </tr>
            ))}
          </Table>
          <p className="text-xs text-ink-3">
            {t("synthetic.utilityRows", { train: count(result.train_rows), synthetic: count(result.synthetic_rows), test: count(result.test_rows) })}
          </p>
        </div>
      )}
    </div>
  );
}

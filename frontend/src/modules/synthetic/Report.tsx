import { Link } from "@tanstack/react-router";
import { Database, Download } from "lucide-react";
import type { ReactNode } from "react";

import type { SyntheticReport, SyntheticRun } from "../../api/client";
import { useSyntheticActions, useSyntheticPreview } from "../../api/hooks";
import { Plot } from "../../charts/Plot";
import { t, type MessageKey } from "../../lib/i18n";
import { Button } from "../../ui/Button";
import { ErrorNote } from "../../ui/fields";
import { InfoTip } from "../../ui/InfoTip";
import { Tabs } from "../../ui/Tabs";
import { ColumnsTab } from "./ColumnsTab";
import { meanSpreadFigure, pcaFigure } from "./figures";
import { count, pct, tone, toneText } from "./format";
import { LinksTab } from "./LinksTab";
import { PrivacyTab, UtilityTab } from "./PrivacyTab";
import { TABS, type Tab } from "./search";

/** The four headline figures, each with its verdict in words (spec 023, section 3). */
function Headline({ report }: { report: SyntheticReport }) {
  const { scores, verdicts } = report;
  const figures: { key: string; score: number | null; verdict: string; detail?: string }[] = [
    { key: "diagnostic", score: scores.diagnostic, verdict: verdicts.diagnostic },
    {
      key: "quality",
      score: scores.quality,
      verdict: verdicts.quality,
      detail: `${t("synthetic.shapes")} ${pct(scores.shapes)} · ${t("synthetic.trends")} ${scores.trends === null ? t("synthetic.noStrongLink") : pct(scores.trends)}`,
    },
    { key: "detection", score: scores.detection, verdict: verdicts.detection },
    { key: "privacy", score: scores.privacy, verdict: verdicts.privacy },
  ];
  return (
    <dl className="grid grid-cols-2 border-y border-line lg:grid-cols-4">
      {figures.map((f, i) => (
        <div key={f.key} className={`px-4 py-3 ${i > 0 ? "lg:border-l lg:border-line" : ""} ${i % 2 === 1 ? "border-l border-line lg:border-l" : ""}`}>
          <dt className="flex items-center gap-1 text-xs text-ink-3">
            {t(`synthetic.${f.key}` as MessageKey)}
            <InfoTip label={t(`synthetic.${f.key}` as MessageKey)} text={t(`synthetic.${f.key}Help` as MessageKey)} />
          </dt>
          <dd className={`text-[28px] leading-tight font-semibold tabular-nums ${toneText[tone(f.score)]}`}>{pct(f.score)}</dd>
          <dd className="text-[13px] text-ink-2">{f.verdict}</dd>
          {f.detail && <dd className="mt-0.5 text-xs text-ink-3">{f.detail}</dd>}
        </div>
      ))}
    </dl>
  );
}

export function Table({ caption, head, children }: { caption: string; head: ReactNode[]; children: ReactNode }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-[13px]">
        <caption className="pb-1.5 text-left text-xs font-medium text-ink-2">{caption}</caption>
        <thead>
          <tr className="border-b border-line text-left text-xs text-ink-3">
            {head.map((h, i) => (
              <th key={i} className={`py-1.5 pr-3 font-normal ${i > 0 ? "text-right" : ""}`}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="tabular-nums">{children}</tbody>
      </table>
    </div>
  );
}

const cell = "py-1.5 pr-3 text-right";

function ChecksTab({ report }: { report: SyntheticReport }) {
  const { diagnostic, quality } = report;
  const pairs = [...quality.pair_scores].sort((a, b) => Number(b.meets) - Number(a.meets) || (a.score ?? 1) - (b.score ?? 1));
  return (
    <div className="grid gap-8 xl:grid-cols-2">
      <div className="space-y-8">
        <Table caption={t("synthetic.diagnosticChecks")} head={[t("synthetic.check"), t("synthetic.column"), t("synthetic.score")]}>
          {diagnostic.checks.map((c, i) => (
            <tr key={i} className={`border-b border-line/60 ${c.score < 1 ? "text-bad" : ""}`}>
              <td className="py-1.5 pr-3" title={c.detail}>
                {c.check}
              </td>
              <td className={`${cell} text-ink-2`}>{c.column ?? "–"}</td>
              <td className={cell}>{pct(c.score, c.score < 1 ? 1 : 0)}</td>
            </tr>
          ))}
        </Table>
        <Table
          caption={t("synthetic.coverage")}
          head={[t("synthetic.column"), t("synthetic.rangeCoverage"), t("synthetic.categoryCoverage"), t("synthetic.missingSimilarity"), t("synthetic.outlierCoverage")]}
        >
          {quality.coverage.map((c) => (
            <tr key={c.column} className="border-b border-line/60">
              <td className="py-1.5 pr-3">{c.column}</td>
              <td className={`${cell} ${toneText[tone(c.range)]}`}>{pct(c.range)}</td>
              <td className={`${cell} ${toneText[tone(c.category)]}`}>{pct(c.category)}</td>
              <td className={`${cell} ${toneText[tone(c.missing)]}`}>{pct(c.missing)}</td>
              <td className={`${cell} ${toneText[tone(c.outliers)]}`}>{c.outliers === null ? t("synthetic.noOutlier") : pct(c.outliers)}</td>
            </tr>
          ))}
        </Table>
        <p className="text-xs text-ink-3">{t("synthetic.coverageHelp")}</p>
      </div>
      <div className="space-y-8">
        <Table caption={`${t("synthetic.shapes")} · ${pct(quality.shapes)}`} head={[t("synthetic.column"), t("synthetic.metric"), t("synthetic.score")]}>
          {quality.shape_scores.map((s) => (
            <tr key={s.column} className="border-b border-line/60">
              <td className="py-1.5 pr-3">{s.column}</td>
              <td className={`${cell} text-ink-3`}>{s.metric}</td>
              <td className={`${cell} ${toneText[tone(s.score)]}`}>{pct(s.score)}</td>
            </tr>
          ))}
        </Table>
        <Table
          caption={`${t("synthetic.trends")} · ${quality.trends === null ? t("synthetic.noStrongLink") : pct(quality.trends)}`}
          head={[t("synthetic.pair"), t("synthetic.realLink"), t("synthetic.syntheticLink"), t("synthetic.score"), t("synthetic.meets")]}
        >
          {pairs.slice(0, 60).map((p) => (
            <tr key={`${p.a}-${p.b}`} className={`border-b border-line/60 ${p.meets ? "" : "text-ink-3"}`}>
              <td className="py-1.5 pr-3" title={p.metric}>
                {p.a} · {p.b}
              </td>
              <td className={cell}>{p.real === null ? "–" : p.real.toFixed(2)}</td>
              <td className={cell}>{p.synthetic === null ? "–" : p.synthetic.toFixed(2)}</td>
              <td className={cell}>{pct(p.score)}</td>
              <td className={cell}>{p.meets ? t("synthetic.yes") : t("synthetic.no")}</td>
            </tr>
          ))}
        </Table>
        <p className="text-xs text-ink-3">{t("synthetic.trendsHelp")}</p>
      </div>
    </div>
  );
}

function OverviewTab({ run }: { run: SyntheticRun }) {
  const { overview, header, fitted } = run.report;
  return (
    <div className="space-y-8">
      <dl className="grid grid-cols-2 gap-x-8 gap-y-2 text-[13px] sm:grid-cols-4">
        {[
          [t("synthetic.trainRows"), count(header.real_rows)],
          [t("synthetic.holdoutRows"), count(header.holdout_rows)],
          [t("synthetic.syntheticRows"), count(header.synthetic_rows)],
          [t("synthetic.duplicates"), `${count(header.real_duplicates)} · ${count(header.synthetic_duplicates)}`],
        ].map(([label, value]) => (
          <div key={label}>
            <dt className="text-xs text-ink-3">{label}</dt>
            <dd className="text-ink-1 tabular-nums">{value}</dd>
          </div>
        ))}
      </dl>
      {overview.mean_spread.length > 0 && (
        <div className="grid gap-6 lg:grid-cols-2">
          {(["mean", "std"] as const).map((which) => (
            <figure key={which} className="space-y-1">
              <figcaption className="text-[13px] font-medium text-ink-1">{t(`synthetic.${which}Scatter` as MessageKey)}</figcaption>
              <Plot figure={meanSpreadFigure(overview.mean_spread, which)} height={300} label={t(`synthetic.${which}Scatter` as MessageKey)} />
            </figure>
          ))}
        </div>
      )}
      {overview.pca && (
        <figure className="space-y-1">
          <figcaption className="text-[13px] font-medium text-ink-1">{t("synthetic.pca")}</figcaption>
          <p className="text-xs text-ink-3">{t("synthetic.pcaHelp")}</p>
          <Plot figure={pcaFigure(overview.pca)} height={360} label={t("synthetic.pca")} />
        </figure>
      )}
      <div className="grid gap-8 lg:grid-cols-2">
        <div>
          <h3 className="pb-1.5 text-xs font-medium text-ink-2">{t("synthetic.method")}: {run.method_label}</h3>
          {fitted.device && (
            <p className="text-[13px] text-ink-2">
              {t("synthetic.trainedOn", { device: fitted.device, epochs: String(fitted.epochs ?? "") })}
            </p>
          )}
          {fitted.order.length > 0 && (
            <p className="text-[13px] text-ink-2">
              {t("synthetic.cartOrder")} {fitted.order.join(" → ")}
            </p>
          )}
          {fitted.method === "bayes" && fitted.edges.length > 0 && (
            <ul className="text-[13px] text-ink-2">
              {fitted.edges.map((e) => (
                <li key={`${e.parent}-${e.child}`}>
                  {e.parent} → {e.child} <span className="text-xs text-ink-3">({e.strength.toFixed(3)})</span>
                </li>
              ))}
            </ul>
          )}
          {fitted.notes.map((n) => (
            <p key={n} className="text-xs text-ink-3">
              {n}
            </p>
          ))}
        </div>
        <div>
          <h3 className="pb-1.5 text-xs font-medium text-ink-2">{t("synthetic.leftOut")}</h3>
          {header.left_out.length === 0 ? (
            <p className="text-[13px] text-ink-3">{t("synthetic.nothingLeftOut")}</p>
          ) : (
            <ul className="text-[13px]">
              {header.left_out.map((c) => (
                <li key={c.column} className="border-b border-line/60 py-1">
                  <span className="text-ink-1">{c.column}</span> <span className="text-xs text-ink-3">{c.reason}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

function DataTab({ run, datasetId }: { run: SyntheticRun; datasetId: string }) {
  const preview = useSyntheticPreview(datasetId, run.id, true);
  const actions = useSyntheticActions(datasetId);
  const created = actions.save.data?.dataset_id ?? run.created_dataset_id;
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Button variant="primary" icon={Database} onClick={() => actions.save.mutate(run.id)} disabled={actions.save.isPending}>
          {t("synthetic.saveAsDataset")}
        </Button>
        {(["csv", "parquet"] as const).map((format) => (
          <a
            key={format}
            href={`/api/v1/modules/synthetic/datasets/${datasetId}/runs/${run.id}/download?format=${format}`}
            download
            className="inline-flex h-(--control-h) items-center gap-1.5 rounded-md border border-line bg-surface-1 px-3 text-[13px] text-ink-1 hover:bg-surface-2"
          >
            <Download size={15} strokeWidth={1.5} aria-hidden />
            {t(`synthetic.download.${format}` as MessageKey)}
          </a>
        ))}
        {created && (
          <p className="text-[13px] text-ink-2" role="status">
            {t("synthetic.savedAs")}{" "}
            <Link to="/d/$datasetId" params={{ datasetId: created }} className="text-accent hover:underline">
              {t("synthetic.openDataset")}
            </Link>
          </p>
        )}
      </div>
      {actions.save.error && <ErrorNote>{actions.save.error.message}</ErrorNote>}
      {preview.data && (
        <div className="max-h-[480px] overflow-auto border-y border-line">
          <table className="w-full text-[12px] whitespace-nowrap">
            <caption className="sr-only">{t("synthetic.preview")}</caption>
            <thead className="sticky top-0 bg-surface-0">
              <tr className="border-b border-line text-left text-ink-3">
                {preview.data.columns.map((c) => (
                  <th key={c} className="px-2 py-1.5 font-normal">
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="tabular-nums">
              {preview.data.rows.map((row, i) => (
                <tr key={i} className="border-b border-line/50">
                  {row.map((value, j) => (
                    <td key={j} className={`px-2 py-1 ${value === null ? "text-ink-3" : "text-ink-1"}`}>
                      {value ?? "–"}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {preview.data && (
        <p className="text-xs text-ink-3">{t("synthetic.previewOf", { shown: String(preview.data.rows.length), total: count(preview.data.total) })}</p>
      )}
    </div>
  );
}

export function Report({
  run,
  datasetId,
  tab,
  onTab,
}: {
  run: SyntheticRun;
  datasetId: string;
  tab: Tab;
  onTab: (tab: Tab) => void;
}) {
  const report = run.report;
  const badges: Partial<Record<Tab, string>> = {
    columns: String(report.columns.length),
    checks: report.diagnostic.failures.length ? String(report.diagnostic.failures.length) : undefined,
  };
  return (
    <section className="space-y-4" aria-label={t("synthetic.report")}>
      <p className="text-xs text-ink-3">
        {run.method_label} · {count(run.rows)} {t("synthetic.rowsShort")} · {t("synthetic.seed")} {run.settings.seed} ·{" "}
        {run.seconds.toFixed(1)} s{run.report.fitted.device ? ` · ${run.report.fitted.device}` : ""} · {new Date(run.created_at).toLocaleString("en", { dateStyle: "medium", timeStyle: "short" })}
      </p>
      <Headline report={report} />
      {report.diagnostic.failures.length > 0 && <ErrorNote>{report.diagnostic.failures.join(" ")}</ErrorNote>}
      <Tabs
        label={t("synthetic.report")}
        value={tab}
        items={TABS.map((value) => ({ value, label: t(`synthetic.tab.${value}` as MessageKey), badge: badges[value] }))}
        onChange={onTab}
      >
        {tab === "columns" && <ColumnsTab run={run} datasetId={datasetId} />}
        {tab === "links" && <LinksTab run={run} datasetId={datasetId} />}
        {tab === "checks" && <ChecksTab report={report} />}
        {tab === "privacy" && <PrivacyTab run={run} datasetId={datasetId} />}
        {tab === "utility" && <UtilityTab run={run} datasetId={datasetId} />}
        {tab === "overview" && <OverviewTab run={run} />}
        {tab === "data" && <DataTab run={run} datasetId={datasetId} />}
      </Tabs>
    </section>
  );
}

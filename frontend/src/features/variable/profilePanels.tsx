import { TriangleAlert } from "lucide-react";
import { useMemo } from "react";

import type { CategoricalProfile, DateProfile, IdentifierProfile, TextProfile } from "../../api/client";
import { formatNumber } from "../../charts/figures";
import { Plot } from "../../charts/Plot";
import { formatCount } from "../../lib/format";
import { t } from "../../lib/i18n";
import { calendarFigure, horizontalBars } from "./figures";
import { Metrics, type Metric } from "./Metrics";
import { pLabel } from "./normality";

function pct(part: number, whole: number): string | undefined {
  if (!whole || !part) return undefined;
  const value = (100 * part) / whole;
  return value > 0 && value < 0.1 ? "<0.1%" : `${value.toFixed(value < 10 ? 1 : 0)}%`;
}

export function categoricalMetrics(profile: CategoricalProfile): Metric[] {
  const present = profile.rows - profile.missing;
  return [
    {
      label: t("cat.top"),
      value: profile.top?.label ?? "—",
      note: profile.top ? pct(profile.top.count, present) : undefined,
    },
    { label: t("stat.distinct"), value: formatCount(profile.distinct) },
    { label: t("stat.missing"), value: formatCount(profile.missing), note: pct(profile.missing, profile.rows) },
    {
      label: t("cat.entropy"),
      value: profile.entropy === null ? "—" : `${formatNumber(profile.entropy)} bits`,
      explain: t("cat.explainEntropy"),
    },
    { label: t("cat.evenness"), value: formatNumber(profile.normalized_entropy), explain: t("cat.explainEvenness") },
    { label: t("cat.herfindahl"), value: formatNumber(profile.herfindahl), explain: t("cat.explainHerfindahl") },
    { label: t("cat.rare"), value: formatCount(profile.rare_count), explain: t("cat.rareHint") },
  ];
}

export function CategoricalPanel({ profile }: { profile: CategoricalProfile }) {
  const present = profile.rows - profile.missing;
  return (
    <div className="space-y-3">
      {profile.imbalanced && profile.top && (
        <p className="flex items-start gap-2 rounded-md border border-line bg-surface-1 px-3 py-2 text-ink-1">
          <TriangleAlert size={15} strokeWidth={1.5} className="mt-0.5 shrink-0 text-warn" aria-hidden />
          {t("cat.imbalance", { label: profile.top.label, share: pct(profile.top.count, present) ?? "" })}
        </p>
      )}
      <Metrics items={categoricalMetrics(profile)} />
      {profile.chi2_p !== null && (
        <p className="text-ink-2">
          <span className="text-ink-3">{t("cat.uniform")} · </span>
          {profile.chi2_p < 0.05
            ? t("cat.uniformNo", { p: pLabel(profile.chi2_p) })
            : t("cat.uniformYes", { p: pLabel(profile.chi2_p) })}
        </p>
      )}
      {profile.rare.length > 0 && (
        <p className="text-xs text-ink-3">
          {t("cat.rare")}: <span className="font-mono text-ink-2">{profile.rare.map((bar) => bar.label).join(" · ")}</span>
        </p>
      )}
    </div>
  );
}

export function dateMetrics(profile: DateProfile): Metric[] {
  return [
    { label: t("date.range"), value: profile.min && profile.max ? `${profile.min.slice(0, 10)} → ${profile.max.slice(0, 10)}` : "—" },
    { label: t("date.granularity"), value: profile.granularity },
    { label: t("date.step"), value: profile.step ?? "—" },
    { label: t("date.periods"), value: formatCount(profile.periods) },
    {
      label: t("date.gaps"),
      value: formatCount(profile.gap_count),
      tone: profile.gap_count ? "text-warn" : "text-ok",
    },
    { label: t("stat.missing"), value: formatCount(profile.missing), note: pct(profile.missing, profile.rows) },
    { label: t("date.time"), value: profile.has_time ? t("date.yes") : t("date.no") },
  ];
}

export function DatePanel({ profile }: { profile: DateProfile }) {
  const calendar = useMemo(() => calendarFigure(profile.calendar), [profile.calendar]);
  return (
    <div className="space-y-4">
      <Metrics items={dateMetrics(profile)} />
      {profile.gap_count === 0 ? (
        <p className="text-ink-2">{t("date.noGaps")}</p>
      ) : (
        <p className="text-ink-2">
          <span className="text-ink-3">{t("date.gapList")}: </span>
          <span className="font-mono text-xs">{profile.gaps.join(" · ")}</span>
        </p>
      )}
      {profile.calendar.length > 0 && (
        <figure className="rounded-md border border-line p-2">
          <figcaption className="mb-1 px-1 text-xs text-ink-3">{t("date.calendar")}</figcaption>
          <Plot figure={calendar} height={180} label={t("date.calendar")} />
        </figure>
      )}
    </div>
  );
}

export function TextPanel({ profile }: { profile: TextProfile }) {
  const words = useMemo(() => horizontalBars(profile.words, (tokens) => tokens.text), [profile.words]);
  return (
    <div className="space-y-4">
      <Metrics
        items={[
          { label: t("stat.distinct"), value: formatCount(profile.distinct) },
          { label: t("stat.missing"), value: formatCount(profile.missing), note: pct(profile.missing, profile.rows) },
          {
            label: t("text.lengths"),
            value: `${formatCount(profile.min_length)} – ${formatCount(profile.max_length)}`,
            note: profile.mean_length !== null ? `avg ${formatNumber(profile.mean_length)}` : undefined,
          },
        ]}
      />
      <figure className="rounded-md border border-line p-2">
        <figcaption className="mb-1 px-1 text-xs text-ink-3">{t("text.words")}</figcaption>
        {profile.words.length ? (
          <Plot figure={words} height={Math.max(160, profile.words.length * 20)} label={t("text.words")} />
        ) : (
          <p className="px-1 py-4 text-ink-3">{t("text.noWords")}</p>
        )}
      </figure>
    </div>
  );
}

export function IdentifierPanel({ profile }: { profile: IdentifierProfile }) {
  return (
    <div className="space-y-4">
      <Metrics
        items={[
          { label: t("id.unique"), value: `${profile.unique_pct.toFixed(profile.unique_pct === 100 ? 0 : 2)}%` },
          { label: t("stat.distinct"), value: formatCount(profile.distinct) },
          {
            label: t("id.repeated"),
            value: formatCount(profile.duplicated_values),
            tone: profile.duplicated_values ? "text-warn" : "text-ok",
          },
          { label: t("stat.missing"), value: formatCount(profile.missing), note: pct(profile.missing, profile.rows) },
          { label: t("id.length"), value: `${formatCount(profile.min_length)} – ${formatCount(profile.max_length)}` },
        ]}
      />
      {profile.duplicated_values === 0 ? (
        <p className="text-ok">{t("id.allUnique")}</p>
      ) : (
        <CountTable title={t("id.repeated")} rows={profile.duplicates} />
      )}
      <CountTable title={`${t("id.patterns")} · ${t("id.patternHint")}`} rows={profile.patterns} mono />
    </div>
  );
}

function CountTable({ title, rows, mono = false }: { title: string; rows: { label: string; count: number }[]; mono?: boolean }) {
  return (
    <section>
      <h3 className="mb-1.5 text-xs font-medium text-ink-3">{title}</h3>
      <div className="max-h-72 overflow-y-auto rounded-md border border-line">
        <table className="w-full border-collapse text-[13px]">
          <thead className="sticky top-0 bg-surface-2 text-left text-xs text-ink-3">
            <tr>
              <th scope="col" className="px-3 py-1.5 font-normal">{t("id.value")}</th>
              <th scope="col" className="px-3 py-1.5 text-right font-normal">{t("id.times")}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.label} className="border-t border-line">
                <td className={`max-w-0 truncate px-3 py-1 ${mono ? "font-mono text-xs" : ""}`} title={row.label}>
                  {row.label}
                </td>
                <td className="px-3 py-1 text-right tabular-nums">{formatCount(row.count)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

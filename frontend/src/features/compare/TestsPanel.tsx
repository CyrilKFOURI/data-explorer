import { CircleAlert, CircleCheck, CircleMinus } from "lucide-react";

import type { BivariateTest, Comparison } from "../../api/client";
import { formatNumber } from "../../charts/figures";
import { formatCount } from "../../lib/format";
import { t, type MessageKey } from "../../lib/i18n";
import { pLabel } from "../variable/normality";

const ALPHA = 0.05;

/** What a significant result means, per test family. */
const FOUND: Record<string, MessageKey> = {
  pearson: "btest.found.correlation",
  spearman: "btest.found.correlation",
  kendall: "btest.found.correlation",
  welch_t: "btest.found.difference",
  mann_whitney: "btest.found.difference",
  anova: "btest.found.difference",
  welch_anova: "btest.found.difference",
  kruskal: "btest.found.difference",
  levene: "btest.found.variances",
  chi2: "btest.found.association",
  fisher: "btest.found.association",
};

/** Effect sizes live between -1 and 1 mostly (d can exceed): 3 decimals read better than 2.3e-3. */
function effectValue(value: number): string {
  return Math.abs(value) < 10 ? value.toFixed(3) : formatNumber(value);
}

export function verdict(test: BivariateTest): { text: string; tone: "ok" | "warn" | "none" } {
  if (test.p_value === null) return { text: t("btest.notRun", { reason: test.note ?? "" }), tone: "none" };
  const family = FOUND[test.key] ?? "btest.found.difference";
  if (test.p_value >= ALPHA) return { text: t(`${family}.no` as MessageKey), tone: "none" };
  const size = test.effect?.magnitude;
  if (size === "negligible") return { text: t("btest.significantNegligible", { what: t(family) }), tone: "warn" };
  return { text: size ? `${t(family)} · ${t(`btest.size.${size}`)}` : t(family), tone: "ok" };
}

export function TestsPanel({ result }: { result: Comparison }) {
  const tests = [...result.tests].sort((a, b) => Number(b.recommended) - Number(a.recommended));
  return (
    <aside className="space-y-3" aria-label={t("compare.tests")}>
      <div>
        <h2 className="text-sm font-semibold">{t("compare.tests")}</h2>
        <p className="mt-0.5 text-xs text-ink-3">
          {t("compare.rowsUsed", { rows: formatCount(result.rows), total: formatCount(result.total) })}
          {result.sample ? ` · ${t("compare.sampled", { sample: formatCount(result.sample) })}` : ""}
        </p>
      </div>
      {tests.length === 0 ? (
        <p className="text-ink-2">{result.message ?? t("compare.noTest")}</p>
      ) : (
        <ul className="space-y-2">
          {tests.map((test) => (
            <TestCard key={test.key} test={test} />
          ))}
        </ul>
      )}
      {tests.length > 0 && result.message && <p className="text-xs text-ink-3">{result.message}</p>}
      <p className="text-xs leading-relaxed text-ink-3">{t("compare.alphaNote")}</p>
    </aside>
  );
}

function TestCard({ test }: { test: BivariateTest }) {
  const { text, tone } = verdict(test);
  const Icon = tone === "ok" ? CircleCheck : tone === "warn" ? CircleAlert : CircleMinus;
  const color = tone === "ok" ? "text-ok" : tone === "warn" ? "text-warn" : "text-ink-3";
  return (
    <li className={`rounded-md border bg-surface-1 px-3 py-2.5 ${test.recommended ? "border-accent" : "border-line"}`}>
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-medium text-ink-1">{t(`btest.${test.key}` as MessageKey)}</h3>
        {test.recommended && (
          <span className="shrink-0 rounded-full bg-accent-soft px-2 py-0.5 text-[11px] font-medium text-ink-1">
            {t("compare.recommended")}
          </span>
        )}
      </div>
      <p className={`mt-1 flex items-start gap-1.5 text-[13px] ${color}`}>
        <Icon size={14} strokeWidth={1.75} className="mt-0.5 shrink-0" aria-hidden />
        <span>{text}</span>
      </p>
      {test.p_value !== null && (
        <dl className="mt-1.5 flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-ink-2 tabular-nums">
          <div className="flex gap-1">
            <dt className="sr-only">{t("normality.pvalue")}</dt>
            <dd className="text-ink-1">{pLabel(test.p_value)}</dd>
          </div>
          <div className="flex gap-1">
            <dt className="text-ink-3">{t("compare.statistic")}</dt>
            <dd>{formatNumber(test.statistic)}</dd>
          </div>
          {test.effect && test.effect.value !== null && (
            <div className="flex gap-1">
              <dt className="text-ink-3">{test.effect.name} =</dt>
              <dd className="text-ink-1">{effectValue(test.effect.value)}</dd>
            </div>
          )}
          <div className="flex gap-1">
            <dt className="text-ink-3">n =</dt>
            <dd>{formatCount(test.n)}</dd>
          </div>
        </dl>
      )}
      <details className="mt-1.5 text-xs text-ink-2">
        <summary className="cursor-pointer text-ink-3 hover:text-ink-1">{t("normality.how")}</summary>
        <p className="mt-1 leading-relaxed">{t(`btest.${test.key}.detail` as MessageKey)}</p>
        {test.note && test.p_value !== null && <p className="mt-1 text-ink-3">{test.note}</p>}
      </details>
    </li>
  );
}

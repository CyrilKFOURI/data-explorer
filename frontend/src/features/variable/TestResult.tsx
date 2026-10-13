import { CircleAlert, CircleCheck, CircleMinus } from "lucide-react";

import type { NormalityTest } from "../../api/client";
import { formatNumber } from "../../charts/figures";
import { formatCount } from "../../lib/format";
import { t, type MessageKey } from "../../lib/i18n";
import { rejects, testP } from "./normality";

/** Verdict in plain words first, then the numbers, then the method on demand. */
export function TestResult({ test, alpha }: { test: NormalityTest; alpha: number }) {
  const name = t(`test.${test.key}.name` as MessageKey);
  const rejected = rejects(test, alpha);
  const Icon = rejected === null ? CircleMinus : rejected ? CircleAlert : CircleCheck;
  const tone = rejected === null ? "text-ink-3" : rejected ? "text-warn" : "text-ok";
  const verdict =
    rejected === null
      ? t("normality.skipped", { reason: test.note ?? "" })
      : rejected
        ? t("normality.reject")
        : t("normality.accept");

  return (
    <li className="px-3 py-2.5">
      <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-1">
        <div className="min-w-0">
          <h4 className="font-medium text-ink-1">{name}</h4>
          <p className={`mt-0.5 flex items-center gap-1.5 ${tone}`}>
            <Icon size={14} strokeWidth={1.75} aria-hidden />
            <span>{verdict}</span>
          </p>
        </div>
        {test.p_value !== null && (
          <dl className="grid grid-cols-[auto_auto] gap-x-3 text-right text-xs tabular-nums">
            <dt className="text-ink-3">{t("normality.pvalue")}</dt>
            <dd className="text-ink-1">{testP(test)}</dd>
            <dt className="text-ink-3">{t("normality.statistic")}</dt>
            <dd className="text-ink-2">{formatNumber(test.statistic)}</dd>
            <dt className="text-ink-3">n</dt>
            <dd className="text-ink-2">{formatCount(test.n)}</dd>
          </dl>
        )}
      </div>
      <details className="mt-1.5 text-xs text-ink-2">
        <summary className="cursor-pointer text-ink-3 hover:text-ink-1">{t("normality.how")}</summary>
        <p className="mt-1 max-w-prose leading-relaxed">{t(`test.${test.key}.detail` as MessageKey)}</p>
        {test.p_value !== null && test.note && <p className="mt-1 text-ink-3">{test.note}</p>}
        {test.p_value !== null && (
          <p className="mt-1 text-ink-3">
            {t("normality.rule", { op: rejected ? "<" : "≥", alpha: String(alpha) })}
          </p>
        )}
      </details>
    </li>
  );
}

import type { Normality } from "../../api/client";
import { formatCount } from "../../lib/format";
import { t } from "../../lib/i18n";
import { SegmentedControl } from "../../ui/SegmentedControl";
import { ALPHAS, normalitySummary, type Alpha } from "./normality";
import { TestResult } from "./TestResult";

type NormalityPanelProps = {
  normality: Normality;
  alpha: Alpha;
  onAlpha: (alpha: Alpha) => void;
};

export function NormalityPanel({ normality, alpha, onAlpha }: NormalityPanelProps) {
  const level = Number(alpha);
  const sentences = normalitySummary(normality, level);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <p className="max-w-prose text-ink-2">{t("normality.intro")}</p>
        <div className="flex items-center gap-2 text-xs text-ink-3">
          <span>{t("normality.alpha")}</span>
          <SegmentedControl
            label={t("normality.alpha")}
            value={alpha}
            options={ALPHAS.map((value) => ({ value, label: value }))}
            onChange={onAlpha}
          />
        </div>
      </div>

      <div className="rounded-md border border-line bg-surface-2 px-3 py-2.5" aria-live="polite">
        {sentences.map((sentence) => (
          <p key={sentence} className="text-ink-1 first:font-medium [&+p]:mt-1 [&+p]:text-ink-2">
            {sentence}
          </p>
        ))}
        {normality.sample < normality.n && (
          <p className="mt-1 text-xs text-ink-3">
            {t("normality.sample", { sample: formatCount(normality.sample), n: formatCount(normality.n) })}
          </p>
        )}
      </div>

      {normality.tests.length > 0 && (
        <ul className="divide-y divide-line rounded-md border border-line bg-surface-1">
          {normality.tests.map((test) => (
            <TestResult key={test.key} test={test} alpha={level} />
          ))}
        </ul>
      )}
    </div>
  );
}

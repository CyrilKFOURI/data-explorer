import type { Dataset } from "../../api/client";
import { t } from "../../lib/i18n";

/** One word on the state of a dataset; problems with the source win over "ready". */
export function StatusBadge({ dataset }: { dataset: Dataset }) {
  let tone = "text-ok";
  let label = t("status.ready");
  let title: string | undefined;

  if (dataset.status === "importing") {
    tone = "text-ink-2";
    label = t("status.importing", {
      percent: String(Math.round((dataset.job?.progress ?? 0) * 100)),
    });
  } else if (dataset.status === "error") {
    tone = "text-bad";
    label = t("status.error");
    title = dataset.error ?? undefined;
  } else if (dataset.source_state === "changed") {
    tone = "text-warn";
    label = t("status.changed");
  } else if (dataset.source_state === "missing") {
    tone = "text-ink-3";
    label = t("status.missing");
  }

  return (
    <span className={`inline-flex items-center gap-1.5 text-xs ${tone}`} title={title}>
      <span aria-hidden className="size-1.5 rounded-full bg-current" />
      {label}
    </span>
  );
}

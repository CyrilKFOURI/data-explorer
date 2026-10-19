import { Link } from "@tanstack/react-router";

import { useSyntheticOrigin } from "../../api/hooks";
import { t } from "../../lib/i18n";

/** "Synthetic, from <source>" on a dataset created from a synthetic run, linking to the run. */
export function SyntheticOrigin({ datasetId }: { datasetId: string }) {
  const origin = useSyntheticOrigin(datasetId);
  if (!origin.data) return null;
  return (
    <p className="mt-1 text-xs text-ink-2">
      <span className="rounded-full border border-accent px-1.5 text-[11px] text-accent">{t("synthetic.badge")}</span>{" "}
      {t("synthetic.from")}{" "}
      <Link
        to="/d/$datasetId/synthetic"
        params={{ datasetId: origin.data.source_id }}
        search={{ run: origin.data.run_id }}
        className="text-accent hover:underline"
      >
        {origin.data.source_name}
      </Link>
    </p>
  );
}

import { FilterX } from "lucide-react";

import { t } from "../../lib/i18n";
import { Button } from "../../ui/Button";
import { useFilters } from "./useFilters";

/** Shown when the active filters leave no row. */
export function NoRows({ datasetId }: { datasetId: string }) {
  const { clear } = useFilters(datasetId);
  return (
    <div className="flex flex-col items-center gap-2 rounded-lg border border-line bg-surface-1 px-6 py-8 text-center">
      <FilterX size={20} strokeWidth={1.5} className="text-ink-3" aria-hidden />
      <p className="font-medium text-ink-1">{t("filters.emptyTitle")}</p>
      <p className="text-ink-2">{t("filters.emptyBody")}</p>
      <Button variant="primary" onClick={clear} className="mt-1">
        {t("filters.clear")}
      </Button>
    </div>
  );
}

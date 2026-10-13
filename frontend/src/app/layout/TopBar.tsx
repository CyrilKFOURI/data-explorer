import { useParams } from "@tanstack/react-router";

import { useDataset } from "../../api/hooks";
import { FilterButton, FilterChips } from "../../features/filters/FilterBar";
import { t } from "../../lib/i18n";
import { useStoredState } from "../../lib/useStoredState";

export function TopBar() {
  const { datasetId } = useParams({ strict: false });
  const dataset = useDataset(datasetId);
  const ready = Boolean(datasetId && dataset.data?.status === "ready");
  const [showChips, setShowChips] = useStoredState("de.filters.chips", false);

  return (
    <>
      <header className="flex h-(--topbar-h) shrink-0 items-center justify-between gap-4 border-b border-line bg-surface-0 px-6">
        {datasetId && dataset.data ? (
          <span className="truncate font-medium text-ink-1">{dataset.data.name}</span>
        ) : (
          <span className="text-ink-3">{t("topbar.noDataset")}</span>
        )}
        {ready && datasetId && <FilterButton datasetId={datasetId} showChips={showChips} onShowChips={setShowChips} />}
      </header>
      {ready && datasetId && showChips && <FilterChips datasetId={datasetId} />}
    </>
  );
}

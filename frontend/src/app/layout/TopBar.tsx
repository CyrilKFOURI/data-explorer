import { useParams } from "@tanstack/react-router";
import { Search } from "lucide-react";

import { useDataset } from "../../api/hooks";
import { OPEN_PALETTE_EVENT } from "../../features/command/Shortcuts";
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
        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={() => window.dispatchEvent(new Event(OPEN_PALETTE_EVENT))}
            className="inline-flex h-(--control-h) items-center gap-2 rounded-md border border-line bg-surface-1 px-2.5 text-[13px] text-ink-3 hover:bg-surface-2 hover:text-ink-1"
          >
            <Search size={14} strokeWidth={1.5} aria-hidden />
            <span className="hidden md:inline">{t("palette.open")}</span>
            <kbd className="hidden rounded border border-line px-1 text-[11px] md:inline">Ctrl K</kbd>
          </button>
          {ready && datasetId && <FilterButton datasetId={datasetId} showChips={showChips} onShowChips={setShowChips} />}
        </div>
      </header>
      {ready && datasetId && showChips && <FilterChips datasetId={datasetId} />}
    </>
  );
}

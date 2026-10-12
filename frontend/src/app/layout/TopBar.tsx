import { useParams } from "@tanstack/react-router";

import { useDataset } from "../../api/hooks";
import { t } from "../../lib/i18n";

export function TopBar() {
  const { datasetId } = useParams({ strict: false });
  const dataset = useDataset(datasetId);

  return (
    <header className="flex h-(--topbar-h) shrink-0 items-center border-b border-line bg-surface-0 px-6">
      {datasetId && dataset.data ? (
        <span className="truncate font-medium text-ink-1">{dataset.data.name}</span>
      ) : (
        <span className="text-ink-3">{t("topbar.noDataset")}</span>
      )}
    </header>
  );
}

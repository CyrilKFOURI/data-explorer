import { t } from "../../lib/i18n";

export function TopBar() {
  return (
    <header className="flex h-(--topbar-h) shrink-0 items-center border-b border-line bg-surface-0 px-6">
      <span className="text-ink-3">{t("topbar.noDataset")}</span>
    </header>
  );
}

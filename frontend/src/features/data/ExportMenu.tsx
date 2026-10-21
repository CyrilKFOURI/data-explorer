import * as Menu from "@radix-ui/react-dropdown-menu";
import { Check, ChevronDown, Download, FileCode, FileSpreadsheet, FileText, Sigma, type LucideIcon } from "lucide-react";
import { useState } from "react";

import { exportUrl, summaryUrl, type ExportFormat, type RowsView } from "../../api/client";
import type { Condition } from "../../api/filters";
import { formatCount } from "../../lib/format";
import { t } from "../../lib/i18n";
import { ReportProgress } from "../report/ReportButton";
import { useReport } from "../report/useReport";

export const EXCEL_ROWS = 1_048_575;

type ExportMenuProps = {
  datasetId: string;
  view: RowsView;
  filters: Condition[];
  total: number;
  visible: string[];
  allColumns: number;
};

const FORMATS: { format: ExportFormat; label: string; icon: LucideIcon }[] = [
  { format: "csv", label: "CSV", icon: FileText },
  { format: "parquet", label: "Parquet", icon: FileText },
  { format: "xlsx", label: "Excel", icon: FileSpreadsheet },
];
const itemClass =
  "flex cursor-default items-center gap-2.5 rounded-md px-2.5 py-1.5 text-[13px] text-ink-1 outline-none data-[disabled]:cursor-not-allowed data-[disabled]:opacity-45 data-[highlighted]:bg-surface-2";

/** Export what the table shows (filters, mode, search, sort) or the column summary. */
export function ExportMenu({ datasetId, view, filters, total, visible, allColumns }: ExportMenuProps) {
  const [onlyVisible, setOnlyVisible] = useState(true);
  const columns = onlyVisible && visible.length < allColumns ? visible : null;
  const report = useReport(datasetId);
  return (
    <span className="inline-flex items-center gap-3">
    <ReportProgress report={report} />
    <Menu.Root>
      <Menu.Trigger className="inline-flex h-(--control-h) items-center gap-1.5 rounded-md border border-line bg-surface-1 px-2.5 text-[13px] text-ink-1 hover:bg-surface-2 data-[state=open]:bg-surface-2">
        <Download size={14} strokeWidth={1.5} aria-hidden />
        {t("data.export")}
        <ChevronDown size={13} strokeWidth={1.5} className="text-ink-3" aria-hidden />
      </Menu.Trigger>
      <Menu.Portal>
        <Menu.Content
          align="end"
          sideOffset={4}
          className="z-50 w-72 rounded-lg border border-line bg-surface-1 p-1 shadow-[0_12px_32px_-12px_rgb(0_0_0/0.35)]"
        >
          <Menu.Label className="px-2.5 pt-1.5 pb-1 text-xs text-ink-3">
            {t("data.exportRows", { rows: formatCount(total) })}
          </Menu.Label>
          {FORMATS.map(({ format, label, icon: Icon }) => {
            const tooMany = format === "xlsx" && total > EXCEL_ROWS;
            return (
              <Menu.Item key={format} asChild disabled={tooMany || total === 0} className={itemClass}>
                <a href={exportUrl(datasetId, format, view, columns, filters)} download>
                  <Icon size={14} strokeWidth={1.5} className="text-ink-3" aria-hidden />
                  {label}
                  {tooMany && <span className="ml-auto text-xs text-ink-3">{t("data.excelLimit")}</span>}
                </a>
              </Menu.Item>
            );
          })}
          {visible.length < allColumns && (
            <Menu.CheckboxItem
              checked={onlyVisible}
              onCheckedChange={setOnlyVisible}
              onSelect={(event) => event.preventDefault()}
              className={`${itemClass} text-ink-2`}
            >
              <span className="inline-flex size-3.5 items-center justify-center rounded-sm border border-line">
                <Menu.ItemIndicator>
                  <Check size={11} strokeWidth={2} className="text-accent" aria-hidden />
                </Menu.ItemIndicator>
              </span>
              {t("data.onlyVisible", { count: String(visible.length), total: String(allColumns) })}
            </Menu.CheckboxItem>
          )}
          <Menu.Separator className="my-1 h-px bg-line" />
          <Menu.Item asChild className={itemClass}>
            <a href={summaryUrl(datasetId, filters)} download>
              <Sigma size={14} strokeWidth={1.5} className="text-ink-3" aria-hidden />
              {t("data.exportSummary")}
            </a>
          </Menu.Item>
          <Menu.Item onSelect={report.start} disabled={report.running} className={itemClass} title={t("report.hint")}>
            <FileCode size={14} strokeWidth={1.5} className="text-ink-3" aria-hidden />
            {t("report.menu")}
          </Menu.Item>
        </Menu.Content>
      </Menu.Portal>
    </Menu.Root>
    </span>
  );
}

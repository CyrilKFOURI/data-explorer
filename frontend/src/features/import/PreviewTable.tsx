import type { ColumnInfo } from "../../api/client";
import { t } from "../../lib/i18n";

type PreviewTableProps = {
  columns: ColumnInfo[];
  rows: (string | null)[][];
  excluded?: Set<string>;
  onToggleColumn?: (column: string) => void;
};

/** Compact read-only grid of raw values; optionally lets the user exclude columns. */
export function PreviewTable({ columns, rows, excluded, onToggleColumn }: PreviewTableProps) {
  return (
    <div className="overflow-auto rounded-md border border-line">
      <table className="w-max min-w-full border-collapse text-[12.5px]">
        <thead className="sticky top-0 bg-surface-2">
          <tr>
            {columns.map((column) => {
              const off = excluded?.has(column.name) ?? false;
              return (
                <th key={column.name} scope="col" className="border-b border-line p-0 text-left font-normal">
                  {onToggleColumn ? (
                    <button
                      type="button"
                      aria-pressed={!off}
                      title={off ? t("preview.include") : t("preview.exclude")}
                      onClick={() => onToggleColumn(column.name)}
                      className={`block w-full px-2.5 py-1.5 text-left hover:bg-surface-1 ${off ? "opacity-40" : ""}`}
                    >
                      <ColumnHeader column={column} off={off} />
                    </button>
                  ) : (
                    <div className="px-2.5 py-1.5">
                      <ColumnHeader column={column} off={false} />
                    </div>
                  )}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex} className="border-b border-line last:border-b-0">
              {row.map((value, columnIndex) => {
                const column = columns[columnIndex];
                const off = column ? (excluded?.has(column.name) ?? false) : false;
                return (
                  <td
                    key={columnIndex}
                    title={value ?? undefined}
                    className={`max-w-56 truncate px-2.5 py-1 tabular-nums ${off ? "text-ink-3 opacity-40" : ""}`}
                  >
                    {value ?? <span className="text-ink-3">—</span>}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ColumnHeader({ column, off }: { column: ColumnInfo; off: boolean }) {
  return (
    <>
      <span className={`block font-mono text-xs font-medium text-ink-1 ${off ? "line-through" : ""}`}>
        {column.name}
      </span>
      <span className="block text-[11px] text-ink-3 lowercase">{column.dtype}</span>
    </>
  );
}

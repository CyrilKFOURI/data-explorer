import { Bookmark, Pencil, Plus, Trash2, X } from "lucide-react";
import { useState } from "react";

import type { Column } from "../../api/client";
import { useDeleteSavedFilter, useSavedFilters, useSaveFilter } from "../../api/hooks";
import { formatCount } from "../../lib/format";
import { t } from "../../lib/i18n";
import { Button } from "../../ui/Button";
import { Checkbox, TextInput } from "../../ui/fields";
import { ConditionEditor } from "./ConditionEditor";
import { describe } from "./conditions";
import { useFilters } from "./useFilters";

type FilterPanelProps = {
  datasetId: string;
  columns: Column[];
  rows?: number;
  totalRows?: number;
  showChips: boolean;
  onShowChips: (show: boolean) => void;
};

/** Active filters (edit, remove), a new filter, saved filters. */
export function FilterPanel({ datasetId, columns, rows, totalRows, showChips, onShowChips }: FilterPanelProps) {
  const { conditions, set, add, replace, remove, clear } = useFilters(datasetId);
  const [editing, setEditing] = useState<number | "new" | null>(conditions.length ? null : "new");
  const filterable = columns.filter((c) => !c.excluded && c.type !== "ignored");

  return (
    <div className="flex max-h-[min(70dvh,640px)] flex-col">
      <header className="flex items-center justify-between gap-3 border-b border-line px-4 py-2.5">
        <div>
          <h2 className="text-sm font-semibold">{t("filters.title")}</h2>
          <p className="text-xs text-ink-3">
            {conditions.length && rows !== undefined && totalRows !== undefined
              ? t("filters.rows", { rows: formatCount(rows), total: formatCount(totalRows) })
              : t("filters.logic")}
          </p>
        </div>
        {conditions.length > 0 && (
          <Button variant="ghost" onClick={clear}>
            {t("filters.clear")}
          </Button>
        )}
      </header>

      <div className="flex-1 space-y-3 overflow-y-auto px-4 py-3">
        {conditions.length > 0 && (
          <ul className="space-y-1.5" aria-label={t("filters.active")}>
            {conditions.map((condition, index) =>
              editing === index ? (
                <li key={index} className="rounded-md border border-accent p-2.5">
                  <ConditionEditor
                    datasetId={datasetId}
                    columns={filterable}
                    initial={condition}
                    onSave={(next) => {
                      replace(index, next);
                      setEditing(null);
                    }}
                    onCancel={() => setEditing(null)}
                  />
                </li>
              ) : (
                <li key={index} className="flex items-center gap-1 rounded-md border border-line bg-surface-2 py-1 pr-1 pl-2.5">
                  {index > 0 && <span className="mr-1 text-[11px] font-medium text-ink-3">{t("filters.and")}</span>}
                  <span className="min-w-0 flex-1 truncate font-mono text-xs text-ink-1" title={describe(condition)}>
                    {describe(condition)}
                  </span>
                  <Button variant="ghost" icon={Pencil} iconOnly aria-label={t("filters.edit", { filter: describe(condition) })} onClick={() => setEditing(index)} />
                  <Button variant="ghost" icon={X} iconOnly aria-label={t("filters.remove", { filter: describe(condition) })} onClick={() => remove(index)} />
                </li>
              ),
            )}
          </ul>
        )}

        {editing === "new" ? (
          <div className="rounded-md border border-line p-2.5">
            <ConditionEditor
              datasetId={datasetId}
              columns={filterable}
              onSave={(condition) => {
                add(condition);
                setEditing(null);
              }}
              onCancel={() => setEditing(null)}
            />
          </div>
        ) : (
          <Button icon={Plus} onClick={() => setEditing("new")} disabled={!filterable.length}>
            {t("filters.add")}
          </Button>
        )}

        <SavedFilters datasetId={datasetId} hasFilters={conditions.length > 0} onApply={set} conditions={conditions} />
      </div>

      <footer className="border-t border-line px-4 py-2 text-xs text-ink-2">
        <Checkbox label={t("filters.showChips")} checked={showChips} onChange={(event) => onShowChips(event.target.checked)} />
      </footer>
    </div>
  );
}

function SavedFilters({
  datasetId,
  hasFilters,
  conditions,
  onApply,
}: {
  datasetId: string;
  hasFilters: boolean;
  conditions: Parameters<ReturnType<typeof useFilters>["set"]>[0];
  onApply: (conditions: Parameters<ReturnType<typeof useFilters>["set"]>[0]) => void;
}) {
  const saved = useSavedFilters(datasetId);
  const save = useSaveFilter(datasetId);
  const remove = useDeleteSavedFilter(datasetId);
  const [name, setName] = useState("");
  const items = saved.data ?? [];

  if (!hasFilters && !items.length) return null;
  return (
    <section className="space-y-1.5 border-t border-line pt-3">
      <h3 className="flex items-center gap-1.5 text-xs font-medium text-ink-3">
        <Bookmark size={13} strokeWidth={1.5} aria-hidden />
        {t("filters.saved")}
      </h3>
      {hasFilters && (
        <form
          className="flex gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            if (name.trim()) save.mutate({ name: name.trim(), conditions }, { onSuccess: () => setName("") });
          }}
        >
          <TextInput
            aria-label={t("filters.saveName")}
            placeholder={t("filters.saveName")}
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="flex-1"
          />
          <Button type="submit" disabled={!name.trim() || save.isPending}>
            {t("filters.save")}
          </Button>
        </form>
      )}
      {save.isError && <p className="text-xs text-bad">{save.error.message}</p>}
      {items.length > 0 && (
        <ul className="space-y-0.5">
          {items.map((item) => (
            <li key={item.id} className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => onApply(item.conditions)}
                title={item.conditions.map(describe).join(" AND ")}
                className="min-w-0 flex-1 truncate rounded-md px-2 py-1 text-left text-[13px] text-ink-1 hover:bg-surface-2"
              >
                {item.name}
                <span className="ml-2 text-xs text-ink-3">{t("filters.count", { count: String(item.conditions.length) })}</span>
              </button>
              <Button variant="ghost" icon={Trash2} iconOnly aria-label={t("filters.deleteSaved", { name: item.name })} onClick={() => remove.mutate(item.id)} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

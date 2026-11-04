import { useCallback, useEffect, useState } from "react";

import type { Column, ColumnChange } from "../../api/client";
import { useUpdateColumns } from "../../api/hooks";

const MAX_HISTORY = 50;

/** The change that restores a column to how it was before `change`. */
export function inverseOf(column: Column, change: ColumnChange): ColumnChange {
  const previous: ColumnChange = { name: column.name };
  if (change.reset || change.type != null) previous.type = column.type;
  if (change.reset || change.role != null) previous.role = column.role ?? "";
  if (change.reset || change.order != null) previous.order = column.order ?? [];
  if (change.excluded != null) previous.excluded = column.excluded;
  return previous;
}

function isEditable(target: EventTarget | null): boolean {
  return (
    target instanceof HTMLElement &&
    (target.isContentEditable || ["INPUT", "SELECT", "TEXTAREA"].includes(target.tagName))
  );
}

/** Apply column corrections with an undo stack (button and Ctrl/Cmd+Z). */
export function useColumnHistory(datasetId: string, columns: Column[]) {
  const update = useUpdateColumns(datasetId);
  const [history, setHistory] = useState<ColumnChange[][]>([]);

  const apply = useCallback(
    (changes: ColumnChange[]) => {
      const byName = new Map(columns.map((column) => [column.name, column]));
      const inverse = changes.flatMap((change) => {
        const column = byName.get(change.name);
        return column ? [inverseOf(column, change)] : [];
      });
      update.mutate(changes, {
        onSuccess: () => setHistory((current) => [...current.slice(-MAX_HISTORY + 1), inverse]),
      });
    },
    [columns, update],
  );

  const undo = useCallback(() => {
    const last = history.at(-1);
    if (!last || update.isPending) return;
    update.mutate(last, { onSuccess: () => setHistory((current) => current.slice(0, -1)) });
  }, [history, update]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "z" && !isEditable(event.target)) {
        event.preventDefault();
        undo();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [undo]);

  return { apply, undo, canUndo: history.length > 0, pending: update.isPending, error: update.error };
}

import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

import { t } from "../../lib/i18n";
import { Button } from "../../ui/Button";
import { Dialog } from "../../ui/Dialog";

type OrderDialogProps = {
  column: string;
  values: string[];
  onSave: (order: string[]) => void;
  onClose: () => void;
};

/** Reorder the categories of an ordinal column, smallest first. */
export function OrderDialog({ column, values, onSave, onClose }: OrderDialogProps) {
  const [order, setOrder] = useState(values);

  const move = (index: number, offset: number) =>
    setOrder((current) => {
      const next = [...current];
      const target = index + offset;
      if (target < 0 || target >= next.length) return current;
      [next[index], next[target]] = [next[target] as string, next[index] as string];
      return next;
    });

  return (
    <Dialog
      open
      onOpenChange={(open) => !open && onClose()}
      title={t("columns.orderTitle", { column })}
      description={t("columns.orderHint")}
      size="sm"
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            {t("import.cancel")}
          </Button>
          <Button
            variant="primary"
            onClick={() => {
              onSave(order);
              onClose();
            }}
          >
            {t("datasets.save")}
          </Button>
        </>
      }
    >
      <ol className="divide-y divide-line rounded-md border border-line">
        {order.map((value, index) => (
          <li key={value} className="flex items-center gap-2 px-3 py-1.5">
            <span className="w-5 text-right text-xs text-ink-3 tabular-nums">{index + 1}</span>
            <span className="min-w-0 flex-1 truncate">{value}</span>
            <Button
              variant="ghost"
              icon={ChevronUp}
              iconOnly
              aria-label={t("columns.moveUp", { value })}
              disabled={index === 0}
              onClick={() => move(index, -1)}
            />
            <Button
              variant="ghost"
              icon={ChevronDown}
              iconOnly
              aria-label={t("columns.moveDown", { value })}
              disabled={index === order.length - 1}
              onClick={() => move(index, 1)}
            />
          </li>
        ))}
      </ol>
    </Dialog>
  );
}

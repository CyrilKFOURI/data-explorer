import * as Menu from "@radix-ui/react-dropdown-menu";
import { Link } from "@tanstack/react-router";
import {
  ArrowDown,
  ArrowDownWideNarrow,
  ArrowUp,
  ArrowUpNarrowWide,
  EyeOff,
  Filter,
  MoreVertical,
  Pin,
  PinOff,
  SquareArrowOutUpRight,
  X,
  type LucideIcon,
} from "lucide-react";

import type { Column } from "../../api/client";
import { t } from "../../lib/i18n";
import { Sparkline } from "../columns/Sparkline";
import { TYPE_META } from "../columns/columnTypes";

export type SortState = "asc" | "desc" | null;

type HeaderCellProps = {
  datasetId: string;
  column: Column;
  bars: { label: string; count: number }[];
  sort: SortState;
  pinned: boolean;
  onSort: (sort: SortState) => void;
  onFilter: () => void;
  onHide: () => void;
  onPin: () => void;
};

const NEXT: Record<"none" | "asc" | "desc", SortState> = { none: "asc", asc: "desc", desc: null };
const itemClass =
  "flex cursor-default items-center gap-2.5 rounded-md px-2.5 py-1.5 text-[13px] text-ink-1 outline-none data-[highlighted]:bg-surface-2";

function Item({ icon: Icon, label, onSelect }: { icon: LucideIcon; label: string; onSelect: () => void }) {
  return (
    <Menu.Item onSelect={onSelect} className={itemClass}>
      <Icon size={14} strokeWidth={1.5} className="text-ink-3" aria-hidden />
      {label}
    </Menu.Item>
  );
}

/** Name (click to sort), type icon, distribution, and a menu of column actions. */
export function HeaderCell({ datasetId, column, bars, sort, pinned, onSort, onFilter, onHide, onPin }: HeaderCellProps) {
  const meta = TYPE_META[column.type];
  const Icon = meta.icon;
  const SortIcon = sort === "asc" ? ArrowUp : ArrowDown;
  return (
    <div className="flex h-full min-w-0 flex-col justify-center gap-1 px-2.5">
      <div className="flex min-w-0 items-center gap-1.5">
        <Icon size={13} strokeWidth={1.5} className={`shrink-0 ${meta.tone}`} aria-label={t(meta.label)} />
        <button
          type="button"
          onClick={() => onSort(NEXT[sort ?? "none"])}
          title={t("data.sortBy", { name: column.name })}
          className="min-w-0 truncate text-left font-mono text-xs font-medium text-ink-1 hover:text-accent"
        >
          {column.name}
        </button>
        {sort && <SortIcon size={12} strokeWidth={2} className="shrink-0 text-accent" aria-label={t(`data.sorted.${sort}`)} />}
        {pinned && <Pin size={11} strokeWidth={1.75} className="shrink-0 text-ink-3" aria-label={t("data.pinned")} />}
        <Menu.Root>
          <Menu.Trigger
            aria-label={t("data.columnMenu", { name: column.name })}
            className="ml-auto inline-flex size-5 shrink-0 items-center justify-center rounded text-ink-3 hover:bg-surface-2 hover:text-ink-1 data-[state=open]:bg-surface-2"
          >
            <MoreVertical size={13} strokeWidth={1.5} aria-hidden />
          </Menu.Trigger>
          <Menu.Portal>
            <Menu.Content
              align="end"
              sideOffset={4}
              className="z-50 min-w-48 rounded-lg border border-line bg-surface-1 p-1 shadow-[0_12px_32px_-12px_rgb(0_0_0/0.35)]"
            >
              <Item icon={ArrowUpNarrowWide} label={t("data.sortAsc")} onSelect={() => onSort("asc")} />
              <Item icon={ArrowDownWideNarrow} label={t("data.sortDesc")} onSelect={() => onSort("desc")} />
              {sort && <Item icon={X} label={t("data.sortClear")} onSelect={() => onSort(null)} />}
              <Menu.Separator className="my-1 h-px bg-line" />
              {!column.excluded && <Item icon={Filter} label={t("data.filterColumn")} onSelect={onFilter} />}
              <Item icon={pinned ? PinOff : Pin} label={pinned ? t("data.unpin") : t("data.pin")} onSelect={onPin} />
              <Item icon={EyeOff} label={t("data.hide")} onSelect={onHide} />
              {!column.excluded && (
                <Menu.Item asChild className={itemClass}>
                  <Link to="/d/$datasetId/variable/$column" params={{ datasetId, column: column.name }}>
                    <SquareArrowOutUpRight size={14} strokeWidth={1.5} className="text-ink-3" aria-hidden />
                    {t("data.openVariable")}
                  </Link>
                </Menu.Item>
              )}
            </Menu.Content>
          </Menu.Portal>
        </Menu.Root>
      </div>
      <Sparkline bars={bars} tone={column.excluded ? "fill-line" : "fill-ink-3"} />
    </div>
  );
}

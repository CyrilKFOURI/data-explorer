import { Filter } from "lucide-react";
import { useEffect, useRef } from "react";

import type { ChartAction } from "./fromChart";

type ChartFilterMenuProps = {
  x: number;
  y: number;
  actions: ChartAction[];
  onPick: (action: ChartAction) => void;
  onClose: () => void;
};

/** Small menu at the click position on a chart. */
export function ChartFilterMenu({ x, y, actions, onPick, onClose }: ChartFilterMenuProps) {
  const menu = useRef<HTMLDivElement>(null);

  useEffect(() => {
    menu.current?.querySelector("button")?.focus();
    const onPointer = (event: PointerEvent) => {
      if (!menu.current?.contains(event.target as Node)) onClose();
    };
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && onClose();
    document.addEventListener("pointerdown", onPointer);
    document.addEventListener("keydown", onKey);
    window.addEventListener("scroll", onClose, true);
    return () => {
      document.removeEventListener("pointerdown", onPointer);
      document.removeEventListener("keydown", onKey);
      window.removeEventListener("scroll", onClose, true);
    };
  }, [onClose]);

  return (
    <div
      ref={menu}
      role="menu"
      style={{ left: Math.min(x, window.innerWidth - 240), top: Math.min(y + 8, window.innerHeight - 100) }}
      className="fixed z-50 w-56 rounded-md border border-line bg-surface-1 p-1 shadow-[0_8px_24px_-12px_rgb(0_0_0/0.35)]"
    >
      {actions.map((action) => (
        <button
          key={action.label}
          type="button"
          role="menuitem"
          onClick={() => onPick(action)}
          className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-[13px] text-ink-1 hover:bg-surface-2 focus-visible:bg-surface-2 focus-visible:outline-none"
        >
          <Filter size={13} strokeWidth={1.5} className="shrink-0 text-ink-3" aria-hidden />
          <span className="truncate">{action.label}</span>
        </button>
      ))}
    </div>
  );
}

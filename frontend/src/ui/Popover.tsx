import { useEffect, useRef, type ReactNode } from "react";

type PopoverProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  trigger: ReactNode;
  label: string;
  children: ReactNode;
  align?: "start" | "end";
};

/** A panel anchored under its trigger; closes on Escape or a click outside. */
export function Popover({ open, onOpenChange, trigger, label, children, align = "end" }: PopoverProps) {
  const root = useRef<HTMLDivElement>(null);
  const panel = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onPointer = (event: PointerEvent) => {
      if (root.current && !root.current.contains(event.target as Node)) onOpenChange(false);
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onOpenChange(false);
    };
    document.addEventListener("pointerdown", onPointer);
    document.addEventListener("keydown", onKey);
    panel.current?.querySelector<HTMLElement>("button, input, select, [tabindex]")?.focus();
    return () => {
      document.removeEventListener("pointerdown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open, onOpenChange]);

  return (
    <div ref={root} className="relative">
      {trigger}
      {open && (
        <div
          ref={panel}
          role="dialog"
          aria-label={label}
          className={`absolute top-full z-40 mt-1.5 w-[min(440px,calc(100vw-32px))] rounded-lg border border-line bg-surface-1 shadow-[0_12px_40px_-12px_rgb(0_0_0/0.35)] ${
            align === "end" ? "right-0" : "left-0"
          }`}
        >
          {children}
        </div>
      )}
    </div>
  );
}

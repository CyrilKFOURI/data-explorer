import type { LucideIcon } from "lucide-react";

export type SegmentedOption<T extends string> = {
  value: T;
  label: string;
  icon?: LucideIcon;
};

type SegmentedControlProps<T extends string> = {
  label: string;
  value: T;
  options: SegmentedOption<T>[];
  onChange: (value: T) => void;
  iconOnly?: boolean;
};

/** A small radio group rendered as joined buttons. */
export function SegmentedControl<T extends string>({
  label,
  value,
  options,
  onChange,
  iconOnly = false,
}: SegmentedControlProps<T>) {
  return (
    <div
      role="radiogroup"
      aria-label={label}
      className="inline-flex rounded-md border border-line bg-surface-2 p-0.5"
    >
      {options.map((option) => {
        const selected = option.value === value;
        const Icon = option.icon;
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={selected}
            aria-label={iconOnly ? option.label : undefined}
            title={iconOnly ? option.label : undefined}
            onClick={() => onChange(option.value)}
            className={`inline-flex h-[calc(var(--control-h)-6px)] items-center gap-1.5 rounded-[4px] px-2 text-xs transition-colors ${
              selected
                ? "bg-surface-1 text-ink-1 shadow-[0_0_0_1px_var(--line)]"
                : "text-ink-2 hover:text-ink-1"
            }`}
          >
            {Icon && <Icon size={14} strokeWidth={1.5} aria-hidden />}
            {!iconOnly && option.label}
          </button>
        );
      })}
    </div>
  );
}

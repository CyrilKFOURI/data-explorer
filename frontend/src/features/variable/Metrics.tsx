import { InfoTip } from "../../ui/InfoTip";

export type Metric = { label: string; value: string; note?: string; explain?: string; tone?: string };

/** Key figures in a row of small tiles. */
export function Metrics({ items }: { items: Metric[] }) {
  return (
    <dl className="grid grid-cols-[repeat(auto-fill,minmax(150px,1fr))] gap-2">
      {items.map((item) => (
        <div key={item.label} className="rounded-md border border-line bg-surface-1 px-3 py-2">
          <dt className="flex items-center gap-1 text-xs text-ink-3">
            <span className="truncate">{item.label}</span>
            {item.explain && <InfoTip label={item.label} text={item.explain} />}
          </dt>
          <dd className={`mt-0.5 truncate text-base font-medium tabular-nums ${item.tone ?? "text-ink-1"}`} title={item.value}>
            {item.value}
            {item.note && <span className="ml-1.5 text-xs font-normal text-ink-3">{item.note}</span>}
          </dd>
        </div>
      ))}
    </dl>
  );
}

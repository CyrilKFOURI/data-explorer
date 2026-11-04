type Bar = { label: string; count: number };

/** Tiny bar chart of a column's distribution; the full charts come with the Overview page. */
export function Sparkline({ bars, tone = "fill-ink-3" }: { bars: Bar[]; tone?: string }) {
  if (bars.length === 0) return <span className="inline-block h-5 w-16" aria-hidden />;
  const width = 64;
  const height = 20;
  const max = Math.max(...bars.map((bar) => bar.count), 1);
  const slot = width / bars.length;
  const gap = bars.length > 16 ? 0.5 : 1;
  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className={`shrink-0 ${tone}`}
      role="img"
      aria-label={bars.map((bar) => `${bar.label}: ${bar.count}`).join(", ")}
    >
      {bars.map((bar, index) => {
        const barHeight = bar.count === 0 ? 0 : Math.max(1, (bar.count / max) * height);
        return (
          <rect
            key={index}
            x={index * slot + gap / 2}
            y={height - barHeight}
            width={Math.max(slot - gap, 0.5)}
            height={barHeight}
            rx={0.5}
          >
            <title>{`${bar.label}: ${bar.count}`}</title>
          </rect>
        );
      })}
    </svg>
  );
}

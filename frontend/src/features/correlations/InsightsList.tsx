import { Link } from "@tanstack/react-router";
import { ArrowRight, BarChart3, Copy, Link2, TriangleAlert, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import type { AnalysisType, Insight } from "../../api/client";
import { t, type MessageKey } from "../../lib/i18n";
import { TYPE_META } from "../columns/columnTypes";

type Group = { id: string; title: MessageKey; icon: LucideIcon; kinds: Insight["kind"][] };

const GROUPS: Group[] = [
  { id: "redundant", title: "insights.group.redundant", icon: Copy, kinds: ["redundant"] },
  { id: "links", title: "insights.group.links", icon: Link2, kinds: ["correlated", "group_difference", "associated"] },
  { id: "shape", title: "insights.group.shape", icon: BarChart3, kinds: ["skewed", "imbalanced"] },
  { id: "quality", title: "insights.group.quality", icon: TriangleAlert, kinds: ["missing"] },
];

/** The sentence with each variable name set in its type's colour. */
export function highlight(text: string, columns: string[], typeOf: (name: string) => AnalysisType | undefined): ReactNode[] {
  const names = [...new Set(columns)].sort((a, b) => b.length - a.length);
  if (!names.length) return [text];
  const escaped = names.map((name) => name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const parts = text.split(new RegExp(`(${escaped.join("|")})`, "g"));
  return parts.map((part, index) => {
    if (!names.includes(part)) return part;
    const type = typeOf(part);
    const tone = type ? TYPE_META[type].tone : "text-ink-1";
    return (
      <span key={index} className={`rounded bg-surface-2 px-1 py-px font-mono text-[12px] font-medium ${tone}`}>
        {part}
      </span>
    );
  });
}

type InsightsListProps = {
  datasetId: string;
  insights: Insight[];
  typeOf: (name: string) => AnalysisType | undefined;
};

/** Insights grouped by theme; each sentence links to the chart that backs it. */
export function InsightsList({ datasetId, insights, typeOf }: InsightsListProps) {
  const groups = GROUPS.map((group) => ({ ...group, items: insights.filter((i) => group.kinds.includes(i.kind)) })).filter(
    (group) => group.items.length,
  );

  return (
    <section aria-label={t("insights.title")} className="space-y-2.5">
      <div className="flex items-baseline gap-2">
        <h2 className="text-sm font-semibold">{t("insights.title")}</h2>
        <span className="text-xs text-ink-3 tabular-nums">{insights.length}</span>
      </div>
      {groups.length === 0 ? (
        <p className="rounded-lg border border-line bg-surface-1 px-4 py-3 text-ink-2">{t("insights.none")}</p>
      ) : (
        <div className="grid gap-3 lg:grid-cols-2">
          {groups.map((group) => {
            const Icon = group.icon;
            return (
              <article key={group.id} className="rounded-lg border border-line bg-surface-1">
                <header className="flex items-center gap-2 border-b border-line px-3.5 py-2">
                  <Icon size={14} strokeWidth={1.5} className="text-ink-3" aria-hidden />
                  <h3 className="text-xs font-medium tracking-wide text-ink-2 uppercase">{t(group.title)}</h3>
                  <span className="text-xs text-ink-3 tabular-nums">{group.items.length}</span>
                </header>
                <ul className="divide-y divide-line">
                  {group.items.map((insight) => (
                    <li key={insight.id} className="group flex items-start gap-3 px-3.5 py-2.5">
                      <span
                        aria-hidden
                        className={`mt-2 size-1.5 shrink-0 rounded-full ${insight.severity === "warning" ? "bg-warn" : "bg-accent"}`}
                      />
                      <p className="min-w-0 flex-1 text-[13px] leading-relaxed text-ink-1">
                        {highlight(insight.text, insight.columns, typeOf)}
                      </p>
                      <InsightLink datasetId={datasetId} insight={insight} />
                    </li>
                  ))}
                </ul>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}

function InsightLink({ datasetId, insight }: { datasetId: string; insight: Insight }) {
  const className =
    "mt-0.5 inline-flex shrink-0 items-center gap-1 rounded-md px-1.5 py-0.5 text-xs text-ink-3 transition-colors group-hover:text-accent hover:bg-surface-2";
  const content = (
    <>
      {t("insights.view")}
      <ArrowRight size={12} strokeWidth={1.75} aria-hidden />
    </>
  );
  if (insight.link.page === "compare" && insight.link.y) {
    return (
      <Link
        to="/d/$datasetId/compare"
        params={{ datasetId }}
        search={(previous) => ({ ...previous, x: insight.link.x, y: insight.link.y ?? undefined, z: undefined, color: undefined })}
        className={className}
      >
        {content}
      </Link>
    );
  }
  return (
    <Link to="/d/$datasetId/variable/$column" params={{ datasetId, column: insight.link.x }} className={className}>
      {content}
    </Link>
  );
}

import { Link } from "@tanstack/react-router";
import { ArrowUpRight, EyeOff, Lightbulb, TriangleAlert } from "lucide-react";
import { useState } from "react";

import type { Insight } from "../../api/client";
import { t } from "../../lib/i18n";
import { useStoredState } from "../../lib/useStoredState";
import { Button } from "../../ui/Button";

/** Rule-based insights; each can be hidden ("not useful"), remembered per dataset. */
export function InsightsList({ datasetId, insights }: { datasetId: string; insights: Insight[] }) {
  const [hidden, setHidden] = useStoredState<string[]>(`de.insights.${datasetId}.hidden`, []);
  const [showHidden, setShowHidden] = useState(false);
  const visible = insights.filter((insight) => showHidden || !hidden.includes(insight.id));
  const hiddenCount = insights.filter((insight) => hidden.includes(insight.id)).length;

  return (
    <section aria-label={t("insights.title")} className="space-y-2">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-sm font-semibold">{t("insights.title")}</h2>
        {hiddenCount > 0 && (
          <button type="button" className="text-xs text-ink-3 hover:text-ink-1" onClick={() => setShowHidden(!showHidden)}>
            {showHidden ? t("insights.hideHidden") : t("insights.showHidden", { count: String(hiddenCount) })}
          </button>
        )}
      </div>
      {visible.length === 0 ? (
        <p className="text-ink-2">{insights.length ? t("insights.allHidden") : t("insights.none")}</p>
      ) : (
        <ul className="grid gap-2 md:grid-cols-2">
          {visible.map((insight) => {
            const isHidden = hidden.includes(insight.id);
            const Icon = insight.severity === "warning" ? TriangleAlert : Lightbulb;
            return (
              <li
                key={insight.id}
                className={`flex items-start gap-2.5 rounded-md border border-line bg-surface-1 px-3 py-2.5 ${isHidden ? "opacity-55" : ""}`}
              >
                <Icon
                  size={15}
                  strokeWidth={1.5}
                  className={`mt-0.5 shrink-0 ${insight.severity === "warning" ? "text-warn" : "text-accent"}`}
                  aria-hidden
                />
                <p className="min-w-0 flex-1 text-[13px] leading-relaxed text-ink-1">{insight.text}</p>
                <div className="flex shrink-0 items-center gap-0.5">
                  {insight.link.page === "compare" && insight.link.y ? (
                    <Link
                      to="/d/$datasetId/compare"
                      params={{ datasetId }}
                      search={(previous) => ({ ...previous, x: insight.link.x, y: insight.link.y ?? undefined })}
                      aria-label={t("insights.view")}
                      title={t("insights.view")}
                      className="inline-flex size-(--control-h) items-center justify-center rounded-md text-ink-2 hover:bg-surface-2 hover:text-ink-1"
                    >
                      <ArrowUpRight size={15} strokeWidth={1.5} aria-hidden />
                    </Link>
                  ) : (
                    <Link
                      to="/d/$datasetId/variable/$column"
                      params={{ datasetId, column: insight.link.x }}
                      aria-label={t("insights.view")}
                      title={t("insights.view")}
                      className="inline-flex size-(--control-h) items-center justify-center rounded-md text-ink-2 hover:bg-surface-2 hover:text-ink-1"
                    >
                      <ArrowUpRight size={15} strokeWidth={1.5} aria-hidden />
                    </Link>
                  )}
                  <Button
                    variant="ghost"
                    icon={EyeOff}
                    iconOnly
                    aria-label={isHidden ? t("insights.restore") : t("insights.hide")}
                    title={isHidden ? t("insights.restore") : t("insights.hide")}
                    onClick={() => setHidden(isHidden ? hidden.filter((id) => id !== insight.id) : [...hidden, insight.id])}
                  />
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

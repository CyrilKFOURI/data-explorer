import type { AssociationMatrix } from "../../api/client";
import { t, type MessageKey } from "../../lib/i18n";
import { useStoredState } from "../../lib/useStoredState";

export type Evidence = AssociationMatrix["pairs"][number]["evidence"];
export type ShownLevels = "strong" | "moderate" | "weak";

const RANK: Record<Evidence, number> = { strong: 3, moderate: 2, weak: 1, none: 0 };
const LABELS: Record<Evidence, MessageKey> = {
  strong: "evidence.strong",
  moderate: "evidence.moderate",
  weak: "evidence.weak",
  none: "evidence.none",
};
const HINTS: Record<Evidence, MessageKey> = {
  strong: "evidence.strongHint",
  moderate: "evidence.moderateHint",
  weak: "evidence.weakHint",
  none: "evidence.noneHint",
};

export const evidenceRank = (level: Evidence | null | undefined) => RANK[level ?? "none"];

/** "moderate" shows strong + moderate: each option includes the levels above it. */
export const isShown = (level: Evidence, shown: ShownLevels) => RANK[level] >= RANK[shown];

/** Remembered for the whole app: it is a reading preference, not a property of one dataset. */
export function useShownLevels() {
  return useStoredState<ShownLevels>("de.insights.evidence", "moderate");
}

/** Signal bars plus a word, so the level never relies on colour alone. */
export function EvidenceBadge({ level }: { level: Evidence }) {
  const rank = RANK[level];
  return (
    <span
      title={t(HINTS[level])}
      className={`inline-flex shrink-0 items-center gap-1 rounded px-1.5 py-px text-[11px] font-medium ${
        level === "strong" ? "bg-accent-soft text-ink-1" : level === "moderate" ? "bg-surface-2 text-ink-1" : "text-ink-3"
      }`}
    >
      <span aria-hidden className="inline-flex items-end gap-px">
        {[1, 2, 3].map((bar) => (
          <span
            key={bar}
            className={`w-[3px] rounded-[1px] ${bar === 1 ? "h-1.5" : bar === 2 ? "h-2" : "h-2.5"} ${
              bar <= rank ? (level === "strong" ? "bg-accent" : "bg-ink-2") : "bg-line"
            }`}
          />
        ))}
      </span>
      {t(LABELS[level])}
    </span>
  );
}

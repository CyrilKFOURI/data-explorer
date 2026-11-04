export const TABS = ["columns", "sequences", "links", "checks", "privacy", "utility", "overview", "data"] as const;
export type Tab = (typeof TABS)[number];

/** URL of the Synthetic data page: the run shown and its tab. */
export type SyntheticSearch = { run?: string; tab?: Tab };

export function validateSyntheticSearch(search: Record<string, unknown>): SyntheticSearch {
  const result: SyntheticSearch = {};
  if (typeof search.run === "string" && search.run) result.run = search.run;
  if (typeof search.tab === "string" && (TABS as readonly string[]).includes(search.tab)) result.tab = search.tab as Tab;
  return result;
}

import type { KpiDefinition } from "../../api/client";

/** URL of the KPI page: a saved KPI, and/or the definition shown (edited or unsaved). */
export type KpiSearch = { kpi?: string; def?: KpiDefinition };

export function validateKpiSearch(search: Record<string, unknown>): KpiSearch {
  const result: KpiSearch = {};
  if (typeof search.kpi === "string" && search.kpi) result.kpi = search.kpi;
  const def = search.def as KpiDefinition | undefined;
  if (def && typeof def === "object" && Array.isArray(def.measures) && def.measures.length) result.def = def;
  return result;
}

import { useState } from "react";

/** Starting values of the analysis controls, set in Settings (per browser). */
export type AnalysisDefaults = { topN: number; pageSize: number; alpha: "0.01" | "0.05" | "0.1" };

export const FACTORY_DEFAULTS: AnalysisDefaults = { topN: 10, pageSize: 12, alpha: "0.05" };
export const TOP_NS = [5, 10, 15, 20, 30, 50];
export const PAGE_SIZES = [6, 12, 24, 48];
export const ALPHAS = ["0.01", "0.05", "0.1"] as const;

const KEY = "de.defaults";

/** Saved defaults, each field checked (an unknown value falls back to the factory default). */
export function readDefaults(): AnalysisDefaults {
  try {
    const stored = JSON.parse(localStorage.getItem(KEY) ?? "{}") as Partial<AnalysisDefaults>;
    return {
      topN: TOP_NS.includes(Number(stored.topN)) ? Number(stored.topN) : FACTORY_DEFAULTS.topN,
      pageSize: PAGE_SIZES.includes(Number(stored.pageSize)) ? Number(stored.pageSize) : FACTORY_DEFAULTS.pageSize,
      alpha: ALPHAS.find((value) => value === stored.alpha) ?? FACTORY_DEFAULTS.alpha,
    };
  } catch {
    return FACTORY_DEFAULTS;
  }
}

export function useAnalysisDefaults(): [AnalysisDefaults, (patch: Partial<AnalysisDefaults>) => void] {
  const [value, setValue] = useState(readDefaults);
  const update = (patch: Partial<AnalysisDefaults>) => {
    const next = { ...value, ...patch };
    setValue(next);
    try {
      localStorage.setItem(KEY, JSON.stringify(next));
    } catch {
      // Storage unavailable: the choice applies to this session only.
    }
  };
  return [value, update];
}

import type { AgentLink } from "./api";

/** Where an "Open in …" link goes: a route of the app and its parameters (R-AG-T5). */
export type LinkTarget = {
  to: string;
  params: Record<string, string>;
  search?: Record<string, string>;
};

export function linkTarget(datasetId: string, link: AgentLink): LinkTarget | null {
  const p = link.params ?? {};
  switch (link.page) {
    case "overview":
      return { to: "/d/$datasetId", params: { datasetId } };
    case "columns":
      return { to: "/d/$datasetId/columns", params: { datasetId } };
    case "variable":
      return p.column ? { to: "/d/$datasetId/variable/$column", params: { datasetId, column: p.column } } : null;
    case "compare":
      return { to: "/d/$datasetId/compare", params: { datasetId }, search: p };
    case "correlations":
      return { to: "/d/$datasetId/correlations", params: { datasetId } };
    case "data":
      return { to: "/d/$datasetId/data", params: { datasetId } };
    default:
      return null;
  }
}

const PAGES: Record<string, string> = {
  "": "Overview",
  columns: "Columns",
  variable: "Variable page",
  compare: "Compare",
  correlations: "Correlations",
  data: "Data",
  timeseries: "Time series",
  ml: "Machine learning",
  kpi: "KPI builder",
  synthetic: "Synthetic data",
};

/** The page the user is on, in words, so "explain this chart" makes sense to the agent. */
export function describePage(pathname: string, search: Record<string, unknown>): string | null {
  const match = /^\/d\/[^/]+\/?([^/]*)\/?(.*)$/.exec(pathname);
  if (!match) return null;
  const [, section = "", rest = ""] = match;
  const page = PAGES[section] ?? section;
  const details: string[] = [];
  if (section === "variable" && rest) details.push(`column ${decodeURIComponent(rest)}`);
  for (const key of ["x", "y", "z", "color", "target", "time", "value"]) {
    const value = search[key];
    if (typeof value === "string" && value) details.push(`${key} = ${value}`);
  }
  return details.length ? `${page} (${details.join(", ")})` : page;
}

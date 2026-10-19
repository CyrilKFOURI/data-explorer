import { Gauge } from "lucide-react";

import type { ModuleManifest } from "../types";
import { KpiPage } from "./KpiPage";
import { validateKpiSearch } from "./search";

export const kpiModule: ModuleManifest = {
  id: "kpi",
  scope: "dataset",
  labelKey: "module.kpi.label",
  icon: Gauge,
  path: "/d/$datasetId/kpi",
  component: KpiPage,
  validateSearch: validateKpiSearch,
};

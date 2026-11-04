import { agentPanel } from "./agent/manifest";
import { kpiModule } from "./kpi/manifest";
import { mlModule } from "./ml/manifest";
import { syntheticModule } from "./synthetic/manifest";
import { timeseriesModule } from "./timeseries/manifest";
import type { ModuleManifest, PanelManifest } from "./types";

/** Active modules. Adding a module = creating its folder and listing its manifest here. */
export const modules: ModuleManifest[] = [timeseriesModule, mlModule, kpiModule, syntheticModule];

/** Panels docked beside the pages. Adding one = listing its manifest here. */
export const panels: PanelManifest[] = [agentPanel];

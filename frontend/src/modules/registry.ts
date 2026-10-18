import { mlModule } from "./ml/manifest";
import { timeseriesModule } from "./timeseries/manifest";
import type { ModuleManifest } from "./types";

/** Active modules. Adding a module = creating its folder and listing its manifest here. */
export const modules: ModuleManifest[] = [timeseriesModule, mlModule];

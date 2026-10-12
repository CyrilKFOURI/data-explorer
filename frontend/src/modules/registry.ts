import { helloModule } from "./hello/manifest";
import type { ModuleManifest } from "./types";

/** Active modules. Adding a module = creating its folder and listing its manifest here. */
export const modules: ModuleManifest[] = [helloModule];

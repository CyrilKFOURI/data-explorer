import { FlaskConical } from "lucide-react";

import type { ModuleManifest } from "../types";
import { HelloPage } from "./HelloPage";

/** Demo module proving the registry works. Kept for tests only. */
export const helloModule: ModuleManifest = {
  id: "hello",
  labelKey: "module.hello.label",
  icon: FlaskConical,
  path: "/modules/hello",
  component: HelloPage,
};

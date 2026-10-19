import { Shuffle } from "lucide-react";

import type { ModuleManifest } from "../types";
import { validateSyntheticSearch } from "./search";
import { SyntheticPage } from "./SyntheticPage";

export const syntheticModule: ModuleManifest = {
  id: "synthetic",
  scope: "dataset",
  labelKey: "module.synthetic.label",
  icon: Shuffle,
  path: "/d/$datasetId/synthetic",
  component: SyntheticPage,
  validateSearch: validateSyntheticSearch,
};

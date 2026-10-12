import type { LucideIcon } from "lucide-react";
import type { ReactElement } from "react";

import type { MessageKey } from "../lib/i18n";

/** What a module declares to appear in the sidebar and own a route. */
export type ModuleManifest = {
  id: string;
  labelKey: MessageKey;
  icon: LucideIcon;
  path: `/modules/${string}`;
  component: () => ReactElement;
};

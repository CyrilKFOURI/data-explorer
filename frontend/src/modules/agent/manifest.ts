import type { PanelManifest } from "../types";
import { AgentPanel } from "./AgentPanel";

/** The assistant docks beside every page of a dataset (spec 026). */
export const agentPanel: PanelManifest = {
  id: "agent",
  component: AgentPanel,
};

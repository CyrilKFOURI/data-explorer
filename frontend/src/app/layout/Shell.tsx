import { Outlet } from "@tanstack/react-router";
import { useState } from "react";

import { KeyboardLayer } from "../../features/command/Shortcuts";
import { t } from "../../lib/i18n";
import type { ModuleManifest } from "../../modules/types";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

const COLLAPSED_KEY = "de.sidebarCollapsed";

function readCollapsed(): boolean {
  try {
    return localStorage.getItem(COLLAPSED_KEY) === "true";
  } catch {
    return false;
  }
}

export function Shell({ modules }: { modules: ModuleManifest[] }) {
  const [collapsed, setCollapsed] = useState(readCollapsed);

  const toggle = () => {
    const next = !collapsed;
    setCollapsed(next);
    try {
      localStorage.setItem(COLLAPSED_KEY, String(next));
    } catch {
      // Not persisted when storage is unavailable.
    }
  };

  return (
    <div className="flex h-dvh bg-surface-0 text-ink-1">
      <a
        href="#main"
        className="sr-only z-50 rounded-md bg-accent px-3 py-2 text-accent-ink focus:not-sr-only focus:fixed focus:top-2 focus:left-2"
      >
        {t("nav.skip")}
      </a>
      <Sidebar collapsed={collapsed} onToggle={toggle} modules={modules} />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar />
        <main id="main" tabIndex={-1} className="min-h-0 flex-1 overflow-y-auto outline-none">
          <Outlet />
        </main>
      </div>
      <KeyboardLayer />
    </div>
  );
}

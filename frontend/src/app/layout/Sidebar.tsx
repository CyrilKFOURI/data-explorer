import { Link, useParams } from "@tanstack/react-router";
import {
  Columns3,
  Grid3x3,
  House,
  LayoutGrid,
  PanelLeftClose,
  PanelLeftOpen,
  Rows3,
  ScatterChart,
  Settings,
  type LucideIcon,
} from "lucide-react";

import { ThemeSwitcher } from "../../features/theme/ThemeSwitcher";
import { t, type MessageKey } from "../../lib/i18n";
import type { ModuleManifest } from "../../modules/types";

/** Pages of the open dataset; those without a route yet arrive with features 003–008. */
const DATASET_PAGES: {
  labelKey: MessageKey;
  icon: LucideIcon;
  to?: "/d/$datasetId" | "/d/$datasetId/columns";
}[] = [
  { labelKey: "nav.overview", icon: LayoutGrid, to: "/d/$datasetId" },
  { labelKey: "nav.columns", icon: Columns3, to: "/d/$datasetId/columns" },
  { labelKey: "nav.compare", icon: ScatterChart },
  { labelKey: "nav.correlations", icon: Grid3x3 },
  { labelKey: "nav.data", icon: Rows3 },
];

const itemClass =
  "flex h-(--control-h) items-center gap-2.5 rounded-md px-2 text-ink-2 transition-colors";

type SidebarProps = {
  collapsed: boolean;
  onToggle: () => void;
  modules: ModuleManifest[];
};

export function Sidebar({ collapsed, onToggle, modules }: SidebarProps) {
  const { datasetId } = useParams({ strict: false });
  return (
    <nav
      aria-label={t("nav.label")}
      className={`flex h-full flex-col border-r border-line bg-surface-1 transition-[width] duration-150 ${
        collapsed ? "w-(--sidebar-w-collapsed)" : "w-(--sidebar-w)"
      }`}
    >
      <div className="flex h-(--topbar-h) items-center border-b border-line px-3">
        {collapsed ? (
          <span className="font-mono text-xs font-medium text-ink-1">DE</span>
        ) : (
          <span className="text-[13px] font-semibold tracking-tight text-ink-1">
            {t("app.name")}
          </span>
        )}
      </div>

      <div className="flex-1 space-y-5 overflow-y-auto px-2 py-3">
        <ul className="space-y-0.5">
          <li>
            <NavLink to="/" icon={House} label={t("nav.home")} collapsed={collapsed} />
          </li>
        </ul>

        <NavSection title={t("nav.section.dataset")} collapsed={collapsed}>
          {DATASET_PAGES.map(({ labelKey, icon: Icon, to }) => (
            <li key={labelKey}>
              {datasetId && to ? (
                <Link
                  to={to}
                  params={{ datasetId }}
                  activeOptions={{ exact: true }}
                  title={collapsed ? t(labelKey) : undefined}
                  aria-label={collapsed ? t(labelKey) : undefined}
                  className={`${itemClass} hover:bg-surface-2 hover:text-ink-1`}
                  activeProps={{ className: "bg-accent-soft !text-ink-1 font-medium" }}
                >
                  <Icon size={16} strokeWidth={1.5} aria-hidden />
                  {!collapsed && t(labelKey)}
                </Link>
              ) : (
              <span
                aria-disabled="true"
                title={datasetId ? t("nav.comingSoon") : t("nav.needsDataset")}
                className={`${itemClass} cursor-not-allowed opacity-45`}
              >
                <Icon size={16} strokeWidth={1.5} aria-hidden />
                {!collapsed && t(labelKey)}
              </span>
              )}
            </li>
          ))}
        </NavSection>

        {modules.length > 0 && (
          <NavSection title={t("nav.section.modules")} collapsed={collapsed}>
            {modules.map((module) => (
              <li key={module.id}>
                <NavLink
                  to={module.path}
                  icon={module.icon}
                  label={t(module.labelKey)}
                  collapsed={collapsed}
                />
              </li>
            ))}
          </NavSection>
        )}
      </div>

      <div className="space-y-2 border-t border-line px-2 py-2">
        <NavLink to="/settings" icon={Settings} label={t("nav.settings")} collapsed={collapsed} />
        <div className={`flex items-center gap-1 ${collapsed ? "flex-col" : "justify-between"}`}>
          {!collapsed && <ThemeSwitcher iconOnly />}
          <button
            type="button"
            onClick={onToggle}
            aria-label={collapsed ? t("nav.expand") : t("nav.collapse")}
            title={collapsed ? t("nav.expand") : t("nav.collapse")}
            className="inline-flex size-(--control-h) items-center justify-center rounded-md text-ink-2 hover:bg-surface-2 hover:text-ink-1"
          >
            {collapsed ? (
              <PanelLeftOpen size={16} strokeWidth={1.5} aria-hidden />
            ) : (
              <PanelLeftClose size={16} strokeWidth={1.5} aria-hidden />
            )}
          </button>
        </div>
      </div>
    </nav>
  );
}

function NavSection({
  title,
  collapsed,
  children,
}: {
  title: string;
  collapsed: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      {collapsed ? (
        <div className="mx-2 mb-2 border-t border-line" />
      ) : (
        <h2 className="mb-1 px-2 text-xs text-ink-3">{title}</h2>
      )}
      <ul className="space-y-0.5">{children}</ul>
    </div>
  );
}

function NavLink({
  to,
  icon: Icon,
  label,
  collapsed,
}: {
  to: string;
  icon: LucideIcon;
  label: string;
  collapsed: boolean;
}) {
  return (
    <Link
      to={to}
      title={collapsed ? label : undefined}
      aria-label={collapsed ? label : undefined}
      className={`${itemClass} hover:bg-surface-2 hover:text-ink-1`}
      activeOptions={{ exact: to === "/" }}
      activeProps={{ className: "bg-accent-soft !text-ink-1 font-medium" }}
    >
      <Icon size={16} strokeWidth={1.5} aria-hidden />
      {!collapsed && label}
    </Link>
  );
}

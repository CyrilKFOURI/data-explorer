import {
  createBrowserHistory,
  createRootRoute,
  createRoute,
  createRouter,
  retainSearchParams,
  type RouterHistory,
} from "@tanstack/react-router";

import { validateFilterSearch, type FilterSearch } from "../api/filters";
import { modules as registeredModules } from "../modules/registry";
import type { ModuleManifest } from "../modules/types";
import { ColumnsPage } from "../pages/columns/ColumnsPage";
import { HomePage } from "../pages/home/HomePage";
import { NotFoundPage } from "../pages/not-found/NotFoundPage";
import { OverviewPage } from "../pages/overview/OverviewPage";
import { SettingsPage } from "../pages/settings/SettingsPage";
import { ComparePage, validateCompareSearch } from "../pages/compare/ComparePage";
import { VariablePage } from "../pages/variable/VariablePage";
import { Shell } from "./layout/Shell";

type RouterOptions = {
  history?: RouterHistory;
  modules?: ModuleManifest[];
};

export function createAppRouter({
  history = createBrowserHistory(),
  modules = registeredModules,
}: RouterOptions = {}) {
  const rootRoute = createRootRoute({
    // Filters follow the user from page to page (see api/filters.ts).
    validateSearch: validateFilterSearch,
    search: { middlewares: [retainSearchParams<FilterSearch>(["filters"])] },
    component: () => <Shell modules={modules} />,
    notFoundComponent: NotFoundPage,
  });

  const homeRoute = createRoute({ getParentRoute: () => rootRoute, path: "/", component: HomePage });
  const settingsRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: "/settings",
    component: SettingsPage,
  });
  const datasetRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: "/d/$datasetId",
    component: OverviewPage,
  });
  const columnsRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: "/d/$datasetId/columns",
    component: ColumnsPage,
  });
  const variableRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: "/d/$datasetId/variable/$column",
    component: VariablePage,
  });
  const compareRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: "/d/$datasetId/compare",
    validateSearch: validateCompareSearch,
    component: ComparePage,
  });
  const moduleRoutes = modules.map((module) =>
    createRoute({ getParentRoute: () => rootRoute, path: module.path, component: module.component }),
  );

  return createRouter({
    routeTree: rootRoute.addChildren([
      homeRoute,
      settingsRoute,
      datasetRoute,
      columnsRoute,
      variableRoute,
      compareRoute,
      ...moduleRoutes,
    ]),
    history,
  });
}

export type AppRouter = ReturnType<typeof createAppRouter>;

declare module "@tanstack/react-router" {
  interface Register {
    router: AppRouter;
  }
}

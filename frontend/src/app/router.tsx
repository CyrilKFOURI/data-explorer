import {
  createBrowserHistory,
  createRootRoute,
  createRoute,
  createRouter,
  type RouterHistory,
} from "@tanstack/react-router";

import { modules as registeredModules } from "../modules/registry";
import type { ModuleManifest } from "../modules/types";
import { DatasetPage } from "../pages/dataset/DatasetPage";
import { HomePage } from "../pages/home/HomePage";
import { NotFoundPage } from "../pages/not-found/NotFoundPage";
import { SettingsPage } from "../pages/settings/SettingsPage";
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
    component: DatasetPage,
  });
  const moduleRoutes = modules.map((module) =>
    createRoute({ getParentRoute: () => rootRoute, path: module.path, component: module.component }),
  );

  return createRouter({
    routeTree: rootRoute.addChildren([homeRoute, settingsRoute, datasetRoute, ...moduleRoutes]),
    history,
  });
}

export type AppRouter = ReturnType<typeof createAppRouter>;

declare module "@tanstack/react-router" {
  interface Register {
    router: AppRouter;
  }
}

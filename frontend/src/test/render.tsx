import { QueryClient } from "@tanstack/react-query";
import { createMemoryHistory } from "@tanstack/react-router";
import { render } from "@testing-library/react";

import { App } from "../app/App";
import { createAppRouter } from "../app/router";
import { modules as registered } from "../modules/registry";

export function renderAt(path: string, modules = registered) {
  const router = createAppRouter({
    history: createMemoryHistory({ initialEntries: [path] }),
    modules,
  });
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(<App router={router} queryClient={queryClient} />);
  return router;
}

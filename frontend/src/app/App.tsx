import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "@tanstack/react-router";
import { useState } from "react";

import type { AppRouter } from "./router";

export function App({ router, queryClient }: { router: AppRouter; queryClient?: QueryClient }) {
  const [client] = useState(
    () => queryClient ?? new QueryClient({ defaultOptions: { queries: { staleTime: 30_000 } } }),
  );
  return (
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}

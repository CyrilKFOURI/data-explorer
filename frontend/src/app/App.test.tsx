import { QueryClient } from "@tanstack/react-query";
import { createMemoryHistory } from "@tanstack/react-router";
import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { helloModule } from "../modules/hello/manifest";
import { App } from "./App";
import { createAppRouter } from "./router";

function renderAt(path: string, modules = [helloModule]) {
  const router = createAppRouter({
    history: createMemoryHistory({ initialEntries: [path] }),
    modules,
  });
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<App router={router} queryClient={queryClient} />);
}

function mockHealth(response: Response | Error) {
  const fetchMock = vi.fn(() =>
    response instanceof Error ? Promise.reject(response) : Promise.resolve(response),
  );
  vi.stubGlobal("fetch", fetchMock);
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("App shell", () => {
  it("renders the home page with backend status", async () => {
    mockHealth(Response.json({ status: "ok", version: "0.1.0", db: "ok" }));
    renderAt("/");

    expect(await screen.findByRole("heading", { name: "No dataset yet" })).toBeInTheDocument();
    expect(await screen.findByText("Backend connected · v0.1.0")).toBeInTheDocument();
  });

  it("explains when the backend is unreachable", async () => {
    mockHealth(new TypeError("Failed to fetch"));
    renderAt("/");

    expect(
      await screen.findByText("Backend unreachable. Start it with scripts/dev.ps1."),
    ).toBeInTheDocument();
  });

  it("renders the settings page", async () => {
    mockHealth(Response.json({ status: "ok", version: "0.1.0", db: "ok" }));
    renderAt("/settings");

    expect(await screen.findByRole("heading", { name: "Settings" })).toBeInTheDocument();
    expect(screen.getByRole("radiogroup", { name: "Density" })).toBeInTheDocument();
  });

  it("renders a not-found page for unknown routes", async () => {
    renderAt("/nope");

    expect(await screen.findByRole("heading", { name: "Page not found" })).toBeInTheDocument();
  });

  it("adds registered modules to the sidebar and routes", async () => {
    renderAt("/modules/hello");

    expect(await screen.findByRole("heading", { name: "Hello module" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Hello" })).toBeInTheDocument();
  });

  it("drops a module that is no longer registered", async () => {
    renderAt("/modules/hello", []);

    expect(await screen.findByRole("heading", { name: "Page not found" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Hello" })).not.toBeInTheDocument();
  });
});

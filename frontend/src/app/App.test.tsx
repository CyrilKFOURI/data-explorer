import { screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { dataset, health, mockApi } from "../test/mockApi";
import { renderAt } from "../test/render";

const baseRoutes = { "GET /health": health, "GET /datasets": [], "GET /samples": [] };

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("App shell", () => {
  it("renders the home page with backend status", async () => {
    mockApi(baseRoutes);
    renderAt("/");

    expect(await screen.findByRole("heading", { name: "Datasets" })).toBeInTheDocument();
    expect(screen.getByText("Drop a CSV, Parquet or Excel file")).toBeInTheDocument();
    expect(await screen.findByText("Backend connected · v0.1.0")).toBeInTheDocument();
  });

  it("explains when the backend is unreachable", async () => {
    mockApi({ ...baseRoutes, "GET /health": new TypeError("Failed to fetch") });
    renderAt("/");

    expect(
      await screen.findByText("Backend unreachable. Start it with scripts/dev.ps1."),
    ).toBeInTheDocument();
  });

  it("lists recent datasets with their status", async () => {
    mockApi({
      ...baseRoutes,
      "GET /datasets": [
        dataset(),
        dataset({ id: "d2", name: "old", source_state: "changed" }),
        dataset({ id: "d3", name: "broken", status: "error", error: "Bad file" }),
      ],
    });
    renderAt("/");

    expect(await screen.findByRole("link", { name: "sales" })).toBeInTheDocument();
    expect(screen.getByText("Source changed")).toBeInTheDocument();
    expect(screen.getByText("Failed")).toHaveAttribute("title", "Bad file");
    expect(screen.getAllByText("1,200 × 3")).toHaveLength(3);
  });

  it("renders the settings page", async () => {
    mockApi(baseRoutes);
    renderAt("/settings");

    expect(await screen.findByRole("heading", { name: "Settings" })).toBeInTheDocument();
    expect(screen.getByRole("radiogroup", { name: "Density" })).toBeInTheDocument();
  });

  it("renders a not-found page for unknown routes", async () => {
    mockApi(baseRoutes);
    renderAt("/nope");

    expect(await screen.findByRole("heading", { name: "Page not found" })).toBeInTheDocument();
  });

  it("adds registered modules to the sidebar and routes", async () => {
    mockApi(baseRoutes);
    renderAt("/modules/hello");

    expect(await screen.findByRole("heading", { name: "Hello module" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Hello" })).toBeInTheDocument();
  });

  it("drops a module that is no longer registered", async () => {
    mockApi(baseRoutes);
    renderAt("/modules/hello", []);

    expect(await screen.findByRole("heading", { name: "Page not found" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Hello" })).not.toBeInTheDocument();
  });
});

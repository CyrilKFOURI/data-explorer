import { screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { health, mockApi } from "../../test/mockApi";
import { renderAt } from "../../test/render";

afterEach(() => vi.unstubAllGlobals());

describe("Guide page", () => {
  it("shows the user guide with a table of contents", async () => {
    mockApi({ "GET /health": health, "GET /datasets": [] });
    renderAt("/help");

    expect(await screen.findByRole("heading", { level: 1, name: "User guide" })).toBeInTheDocument();
    const contents = screen.getByRole("navigation", { name: "Contents" });
    expect(within(contents).getByRole("link", { name: "Metrics" })).toHaveAttribute("href", "#metrics");
    expect(screen.getByRole("heading", { level: 2, name: "Filters" })).toHaveAttribute("id", "filters");
    expect(screen.getByRole("heading", { name: "Normality tests" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Guide" })).toHaveAttribute("href", "/help");
  });
});

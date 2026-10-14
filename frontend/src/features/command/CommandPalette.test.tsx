import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { column, roles } from "../../test/columns";
import { dataset, health, mockApi } from "../../test/mockApi";
import { renderAt } from "../../test/render";

const columns = [
  column({ name: "price", position: 0 }),
  column({ name: "country", position: 1, type: "categorical_nominal", detected_type: "categorical_nominal" }),
];

function setup() {
  return mockApi({
    "GET /health": health,
    "GET /datasets": [dataset(), dataset({ id: "d2", name: "fleet" })],
    "GET /datasets/d1": dataset(),
    "GET /datasets/d1/columns": columns,
    "GET /column-roles": roles,
    "GET /settings": { detection: { parse_rate: 0.95, empty_rate: 0.95, discrete_max: 20, identifier_unique: 0.95 } },
    "GET /storage": { workspace: "W", total_bytes: 0, datasets: [] },
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
  delete document.documentElement.dataset.theme;
});

describe("Command palette", () => {
  it("opens with Ctrl+K and jumps to a variable from the keyboard", async () => {
    setup();
    const router = renderAt("/help");
    await screen.findByRole("heading", { level: 1, name: "User guide" });
    await waitFor(() => expect(router.state.location.pathname).toBe("/help"));

    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    const dialog = await screen.findByRole("dialog", { name: "Command palette" });
    const box = within(dialog).getByRole("combobox");
    expect(within(dialog).getByRole("option", { name: /fleet/ })).toBeInTheDocument();
    fireEvent.change(box, { target: { value: "sett" } });
    expect(within(dialog).getAllByRole("option")).toHaveLength(1);
    fireEvent.keyDown(box, { key: "Enter" });

    await waitFor(() => expect(router.state.location.pathname).toBe("/settings"));
    expect(screen.queryByRole("dialog", { name: "Command palette" })).not.toBeInTheDocument();
  });

  it("lists the open dataset's pages and variables, and runs actions", async () => {
    setup();
    const router = renderAt("/d/d1/data");

    fireEvent.click(await screen.findByRole("button", { name: /Search or jump to/ }));
    const dialog = await screen.findByRole("dialog", { name: "Command palette" });
    const box = within(dialog).getByRole("combobox");
    fireEvent.change(box, { target: { value: "countr" } });
    await within(dialog).findByRole("option", { name: /country/ });
    fireEvent.keyDown(box, { key: "Enter" });
    await waitFor(() => expect(router.state.location.pathname).toBe("/d/d1/variable/country"));

    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    const again = await screen.findByRole("dialog", { name: "Command palette" });
    fireEvent.change(within(again).getByRole("combobox"), { target: { value: "theme: dark" } });
    fireEvent.click(within(again).getByRole("option", { name: /Theme: dark/ }));
    expect(document.documentElement.dataset.theme).toBe("dark");
  });

  it("lists the keyboard shortcuts with ?", async () => {
    setup();
    renderAt("/help");
    await screen.findByRole("heading", { level: 1, name: "User guide" });

    fireEvent.keyDown(document.body, { key: "?" });

    const dialog = await screen.findByRole("dialog", { name: "Keyboard shortcuts" });
    expect(within(dialog).getByText("Command palette")).toBeInTheDocument();
    expect(within(dialog).getByText("Open the filters")).toBeInTheDocument();
  });
});

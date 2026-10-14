import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { forwardRef } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { column, roles } from "../../test/columns";
import { dataset, health, mockApi } from "../../test/mockApi";
import { renderAt } from "../../test/render";

vi.mock("../../charts/Plot", () => ({
  Plot: forwardRef<HTMLDivElement, { label: string }>(function Plot({ label }, ref) {
    return <div ref={ref} role="img" aria-label={label} />;
  }),
}));

const columns = [
  column({ name: "price", position: 0 }),
  column({ name: "country", position: 1, type: "categorical_nominal", detected_type: "categorical_nominal" }),
];

const overview = (rows: number) => ({
  rows,
  total_rows: 1200,
  columns: 2,
  used_columns: 2,
  missing_cells: 0,
  missing_pct: 0,
  duplicate_rows: 0,
  duplicate_columns: [],
  size_bytes: 1024,
  types: { numeric_continuous: 1, categorical_nominal: 1 },
  alerts: [],
  column_stats: {},
});

const countries = {
  kind: "bars",
  view: "bars",
  views: ["bars"],
  rows: 1200,
  missing: 0,
  distinct: 2,
  bars: [
    { label: "FR", count: 700 },
    { label: "BE", count: 500 },
  ],
  others: null,
  ordered: false,
  bins: [],
  stats: null,
  box: null,
  step: null,
  steps: [],
  examples: [],
  duplicates: 0,
  message: null,
};

function setup() {
  return mockApi({
    "GET /health": health,
    "GET /datasets/d1": dataset({ types_reviewed_at: "2026-10-13T10:00:00Z" }),
    "POST /datasets/d1/open": dataset(),
    "GET /datasets/d1/columns": columns,
    "GET /column-roles": roles,
    "GET /datasets/d1/overview": () => overview(700),
    "GET /datasets/d1/columns/chart": countries,
    "GET /datasets/d1/columns/summaries": {},
    "GET /datasets/d1/saved-filters": [],
  });
}

const FR = '[{"column":"country","op":"in","negate":false,"values":["FR"]}]';

beforeEach(() => localStorage.clear());
afterEach(() => vi.unstubAllGlobals());

describe("Global filters", () => {
  it("adds a category filter and applies it to every request", async () => {
    const calls = setup();
    renderAt("/d/d1");
    fireEvent.click(await screen.findByRole("button", { name: /^Filter/ }));

    const panel = await screen.findByRole("dialog", { name: "Filters" });
    fireEvent.change(within(panel).getByLabelText("Column"), { target: { value: "country" } });
    fireEvent.click(await within(panel).findByRole("checkbox", { name: /FR/ }));
    fireEvent.click(within(panel).getByRole("button", { name: "Apply" }));

    expect(await within(panel).findByText("country ∈ FR")).toBeInTheDocument();
    await waitFor(() =>
      expect(calls.some((c) => c.key === "GET /datasets/d1/overview" && c.params.get("filters") === FR)).toBe(true),
    );
    expect(await screen.findAllByText("700 / 1,200 rows")).not.toHaveLength(0);
    expect(screen.getByRole("button", { name: /^Filter/ })).toHaveTextContent("1");
  });

  it("keeps one row per value of a combination of columns", async () => {
    const calls = setup();
    renderAt("/d/d1");
    fireEvent.click(await screen.findByRole("button", { name: /^Filter/ }));

    const panel = await screen.findByRole("dialog", { name: "Filters" });
    fireEvent.change(within(panel).getByLabelText("Column"), { target: { value: "country" } });
    fireEvent.change(within(panel).getByLabelText("Condition"), { target: { value: "unique" } });
    fireEvent.change(within(panel).getByLabelText("+ column"), { target: { value: "price" } });
    fireEvent.click(within(panel).getByRole("radio", { name: "Last row" }));
    fireEvent.change(within(panel).getByLabelText("Ordered by"), { target: { value: "price" } });
    fireEvent.click(within(panel).getByRole("button", { name: "Apply" }));

    expect(await within(panel).findByText("country + price · unique (last by price)")).toBeInTheDocument();
    await waitFor(() => {
      const sent = calls.find((c) => c.key === "GET /datasets/d1/overview" && c.params.get("filters"));
      expect(JSON.parse(sent?.params.get("filters") ?? "[]")).toEqual([
        { column: "country", op: "unique", negate: false, columns: ["price"], keep: "last", order_by: "price" },
      ]);
    });
  });

  it("keeps the filters when moving to another page", async () => {
    const calls = setup();
    const filters = encodeURIComponent(JSON.stringify({ dataset: "d1", conditions: JSON.parse(FR) }));
    const router = renderAt(`/d/d1?filters=${filters}`);
    await screen.findByRole("heading", { name: "Overview" });

    fireEvent.click(screen.getByRole("link", { name: "Columns" }));

    await waitFor(() => expect(router.state.location.pathname).toBe("/d/d1/columns"));
    await waitFor(() =>
      expect(calls.some((c) => c.key === "GET /datasets/d1/columns/summaries" && c.params.get("filters") === FR)).toBe(
        true,
      ),
    );
  });

  it("ignores filters that belong to another dataset", async () => {
    const calls = setup();
    const filters = encodeURIComponent(JSON.stringify({ dataset: "other", conditions: JSON.parse(FR) }));
    renderAt(`/d/d1?filters=${filters}`);
    await screen.findByRole("heading", { name: "Overview" });

    await waitFor(() => expect(calls.some((c) => c.key === "GET /datasets/d1/overview")).toBe(true));
    expect(calls.filter((c) => c.key === "GET /datasets/d1/overview").every((c) => !c.params.has("filters"))).toBe(true);
    expect(screen.getByRole("button", { name: /^Filter/ })).not.toHaveTextContent("1");
  });

  it("removes a filter and clears them all", async () => {
    setup();
    const filters = encodeURIComponent(JSON.stringify({ dataset: "d1", conditions: JSON.parse(FR) }));
    const router = renderAt(`/d/d1?filters=${filters}`);
    fireEvent.click(await screen.findByRole("button", { name: /^Filter/ }));

    const panel = await screen.findByRole("dialog", { name: "Filters" });
    fireEvent.click(within(panel).getByRole("button", { name: "Remove country ∈ FR" }));

    await waitFor(() => expect(router.state.location.search).toEqual({}));
  });
});

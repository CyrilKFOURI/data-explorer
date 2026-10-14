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
  column({ name: "units", position: 0 }),
  column({ name: "revenue", position: 1 }),
  column({ name: "store", position: 2, type: "categorical_nominal", detected_type: "categorical_nominal" }),
];

const correlations = {
  matrix: {
    method: "pearson",
    columns: [
      { name: "units", type: "numeric_continuous", role: "num" },
      { name: "revenue", type: "numeric_continuous", role: "num" },
      { name: "store", type: "categorical_nominal", role: "cat" },
    ],
    values: [
      [1, 0.997, 0.7],
      [0.997, 1, 0.69],
      [0.7, 0.69, 1],
    ],
    metrics: [
      [null, "pearson", "eta"],
      ["pearson", null, "eta"],
      ["eta", "eta", null],
    ],
    n: [
      [100, 100, 100],
      [100, 100, 100],
      [100, 100, 100],
    ],
    clustered: [2, 0, 1],
    rows: 100,
    total: 100,
    sampled: false,
    excluded: [{ name: "date", reason: "Dates: compare them with a numeric or category on the Compare page." }],
    truncated: 0,
    pairs: [
      { a: "units", b: "revenue", metric: "pearson", value: 0.997, p_value: 0.0001, n: 100 },
      { a: "units", b: "store", metric: "eta", value: 0.7, p_value: 0.0001, n: 100 },
    ],
  },
  insights: [
    {
      id: "redundant:units|revenue",
      kind: "redundant",
      severity: "warning",
      text: "units and revenue are almost identical (r = 0.997): probably redundant, keep one of them in models.",
      columns: ["units", "revenue"],
      link: { page: "compare", x: "units", y: "revenue" },
      score: 2.9,
    },
    {
      id: "skewed:revenue",
      kind: "skewed",
      severity: "info",
      text: "revenue is strongly skewed to the right.",
      columns: ["revenue"],
      link: { page: "variable", x: "revenue", y: null },
      score: 0.9,
    },
  ],
};

function setup() {
  return mockApi({
    "GET /health": health,
    "GET /datasets/d1": dataset(),
    "GET /datasets/d1/columns": columns,
    "GET /column-roles": roles,
    "GET /datasets/d1/correlations": correlations,
  });
}

beforeEach(() => localStorage.clear());
afterEach(() => vi.unstubAllGlobals());

describe("Correlations page", () => {
  it("shows insights with links to their proof", async () => {
    setup();
    renderAt("/d/d1/correlations");

    const insight = await screen.findByText(/almost identical/);
    const card = insight.closest("li") as HTMLElement;
    expect(within(card).getByRole("link", { name: "View" })).toHaveAttribute(
      "href",
      "/d/d1/compare?x=units&y=revenue",
    );
    const skewed = (screen.getByText(/strongly skewed/).closest("li") as HTMLElement);
    expect(within(skewed).getByRole("link", { name: "View" })).toHaveAttribute("href", "/d/d1/variable/revenue");
  });

  it("groups insights by theme and colours variable names", async () => {
    setup();
    renderAt("/d/d1/correlations");

    expect(await screen.findByRole("heading", { name: "Redundant variables" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Distributions" })).toBeInTheDocument();
    const names = screen.getAllByText("revenue", { selector: "span" });
    expect(names.some((name) => name.className.includes("text-type-numeric"))).toBe(true);
  });

  it("draws the matrix, ranks pairs and lists excluded columns", async () => {
    setup();
    renderAt("/d/d1/correlations");

    expect(await screen.findByRole("img", { name: "Association matrix" })).toBeInTheDocument();
    const table = screen.getByRole("table");
    expect(within(table).getAllByRole("row")).toHaveLength(3);
    expect(within(table).getByText("0.997")).toBeInTheDocument();
    expect(screen.getByText("Columns left out (1)")).toBeInTheDocument();
  });

  it("focuses on a variable and switches method", async () => {
    const calls = setup();
    renderAt("/d/d1/correlations");
    await screen.findByRole("img", { name: "Association matrix" });

    fireEvent.click(screen.getByRole("button", { name: "store" }));
    const ranked = screen.getByRole("list", { name: "Variables most related to store" });
    expect(within(ranked).getAllByRole("listitem")[0]).toHaveTextContent("units");
    expect(within(ranked).getByRole("link", { name: "Compare store with units" })).toHaveAttribute(
      "href",
      "/d/d1/compare?x=store&y=units",
    );

    fireEvent.click(screen.getByRole("radio", { name: "Spearman" }));
    await waitFor(() =>
      expect(calls.some((c) => c.key === "GET /datasets/d1/correlations" && c.params.get("method") === "spearman")).toBe(
        true,
      ),
    );
  });
});

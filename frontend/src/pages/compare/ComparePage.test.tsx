import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { forwardRef } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { BivariateTest } from "../../api/client";
import { verdict } from "../../features/compare/TestsPanel";
import { column, roles } from "../../test/columns";
import { dataset, health, mockApi } from "../../test/mockApi";
import { renderAt } from "../../test/render";

vi.mock("../../charts/Plot", () => ({
  Plot: forwardRef<HTMLDivElement, { label: string }>(function Plot({ label }, ref) {
    return <div ref={ref} role="img" aria-label={label} />;
  }),
}));

const columns = [
  column({ name: "age", position: 0 }),
  column({ name: "income", position: 1 }),
  column({ name: "segment", position: 2, type: "categorical_nominal", detected_type: "categorical_nominal" }),
  column({ name: "comment", position: 3, type: "text", detected_type: "text" }),
];

const test = (overrides: Partial<BivariateTest>): BivariateTest => ({
  key: "pearson",
  statistic: 0.5,
  p_value: 0.001,
  n: 600,
  effect: { name: "r", value: 0.5, magnitude: "large" },
  recommended: false,
  note: null,
  ...overrides,
});

const scatter = {
  kind: "scatter",
  x: "age",
  y: "income",
  z: null,
  color: null,
  roles: { age: "num", income: "num" },
  rows: 551,
  total: 600,
  sample: null,
  group_axis: null,
  points: { x: [1, 2, 3], y: [2, 4, 6], z: null, color: null },
  regression: { slope: 2, intercept: 0, r2: 0.25 },
  density: null,
  groups: [],
  contingency: null,
  series: [],
  step: null,
  tests: [test({}), test({ key: "spearman", p_value: 0.2, effect: { name: "rho", value: 0.05, magnitude: "negligible" } })],
  message: null,
};

function setup() {
  return mockApi({
    "GET /health": health,
    "GET /datasets/d1": dataset(),
    "GET /datasets/d1/columns": columns,
    "GET /column-roles": roles,
    "GET /datasets/d1/compare": scatter,
  });
}

afterEach(() => vi.unstubAllGlobals());

describe("Compare page", () => {
  it("asks for two columns first and hides non-comparable ones", async () => {
    setup();
    renderAt("/d/d1/compare");

    expect(await screen.findByText("Pick an X and a Y column to compare them.")).toBeInTheDocument();
    const x = screen.getByLabelText("X");
    expect(within(x).queryByRole("option", { name: "comment" })).not.toBeInTheDocument();
    expect(within(x).getByRole("option", { name: "segment" })).toBeInTheDocument();
  });

  it("shows the chart and the tests for the chosen pair", async () => {
    const calls = setup();
    renderAt("/d/d1/compare?x=age&y=income");

    expect(await screen.findByRole("img", { name: "income against age" })).toBeInTheDocument();
    expect(screen.getByText("551 of 600 rows have every value")).toBeInTheDocument();
    expect(screen.getByText("Significant correlation · large effect")).toBeInTheDocument();
    expect(screen.getByText("No evidence of a correlation")).toBeInTheDocument();
    expect(screen.getByLabelText(/Linear fit \(R² = 0.250\)/)).toBeChecked();
    const call = calls.find((c) => c.key === "GET /datasets/d1/compare");
    expect(call?.params.get("x")).toBe("age");
    expect(call?.params.get("y")).toBe("income");
  });

  it("swaps X and Y in the URL", async () => {
    setup();
    const router = renderAt("/d/d1/compare?x=age&y=income");
    await screen.findByRole("img", { name: "income against age" });

    fireEvent.click(screen.getByRole("button", { name: "Swap X and Y" }));

    await waitFor(() => expect(router.state.location.search).toMatchObject({ x: "income", y: "age" }));
  });

  it("offers Z only for two numeric columns", async () => {
    setup();
    renderAt("/d/d1/compare?x=age&y=segment");

    expect(await screen.findByLabelText("Z (3D)")).toBeDisabled();
  });
});

describe("test verdicts", () => {
  it("separates significance from importance", () => {
    expect(verdict(test({ effect: { name: "r", value: 0.02, magnitude: "negligible" } })).text).toBe(
      "Significant correlation, but the effect is negligible",
    );
    expect(verdict(test({ key: "anova", p_value: 0.3 })).text).toBe("No evidence that the groups differ");
    expect(verdict(test({ key: "chi2", effect: { name: "V", value: 0.2, magnitude: "medium" } })).text).toBe(
      "The variables are associated · medium effect",
    );
    expect(verdict(test({ p_value: null, note: "Too few rows." })).text).toBe("Not run: Too few rows.");
  });
});

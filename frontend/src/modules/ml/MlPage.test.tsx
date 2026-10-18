import { fireEvent, screen, waitFor } from "@testing-library/react";
import { forwardRef } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { MlRun } from "../../api/client";
import { column, roles } from "../../test/columns";
import { dataset, health, mockApi } from "../../test/mockApi";
import { renderAt } from "../../test/render";
import { verdict } from "./Results";

vi.mock("../../charts/Plot", () => ({
  Plot: forwardRef<HTMLDivElement, { label: string }>(function Plot({ label }, ref) {
    return <div ref={ref} role="img" aria-label={label} />;
  }),
}));

const candidate = (name: string, task: string | null, overrides: Record<string, unknown> = {}) => ({
  name,
  type: "numeric_continuous",
  role: null,
  task,
  reason: task ? null : "Cannot be predicted: an identifier.",
  suggested: false,
  classes: null,
  missing_share: 0,
  ...overrides,
});

const regressionRun = {
  id: "r1",
  dataset_id: "d1",
  target: "price",
  created_at: "2026-10-18T10:00:00Z",
  task: "regression",
  model: "linear_regression",
  settings: { regularization: "none", alpha: 1 },
  preparation: {
    decisions: [
      { column: "price", type: "numeric_continuous", use: false, rules: ["R-SEL-01"], why: ["This is the target."], impute: null, indicator: false, transform: null, encoding: null, scaling: null, order: null },
      { column: "size", type: "numeric_continuous", use: true, rules: ["R-NUM-08"], why: ["Standardised."], impute: "mean", indicator: false, transform: null, encoding: null, scaling: "standard", order: null },
    ],
    inputs: 1,
    excluded: 1,
  },
  train_rows: 80,
  test_rows: 20,
  rows: 100,
  sampled: false,
  seconds: 0.3,
  regression: {
    r2: 0.82,
    mae: 10,
    rmse: 12,
    mape: null,
    baseline_mae: 17,
    baseline_rmse: 20,
    skill: 0.41,
    actual: [1, 2, 3],
    predicted: [1.1, 2.1, 2.9],
    residual_bins: [{ start: -1, end: 1, count: 3 }],
    heteroscedasticity_p: 0.4,
  },
  classification: null,
  coefficients: [{ feature: "size", estimate: 3, std_error: 0.1, low: 2.8, high: 3.2, p_value: 0.0001, vif: 1, per_unit: 0.5, odds_ratio: null }],
  predictions: [{ row: 4, actual: "10", predicted: "11", error: 1, probability: null, correct: null }],
  primary: "r2",
  score: 0.82,
};

function setup() {
  return mockApi({
    "GET /health": health,
    "GET /datasets": [dataset()],
    "GET /datasets/d1": dataset(),
    "GET /datasets/d1/columns": [column({ name: "price" })],
    "GET /column-roles": roles,
    "GET /modules/ml/datasets/d1/targets": {
      candidates: [candidate("price", "regression", { suggested: true }), candidate("vin", null)],
      rows: 100,
    },
    "GET /modules/ml/catalog": [
      {
        key: "linear_regression",
        label: "Linear regression",
        family: "Linear models",
        description: "A weighted sum of the features.",
        tasks: ["regression"],
        settings: [
          { key: "regularization", label: "Regularization", kind: "select", default: "none", level: "essential", options: ["none", "ridge", "lasso"], minimum: null, maximum: null, log: false, why: "", shown_when: null },
        ],
      },
    ],
    "GET /modules/ml/datasets/d1/runs": [],
    "POST /modules/ml/datasets/d1/runs": { id: "job1", status: "running", stage: "loading", run_id: null, error: null },
    "GET /modules/ml/jobs/job1": { id: "job1", status: "done", stage: "saving", run_id: "r1", error: null },
    "GET /modules/ml/datasets/d1/runs/r1": regressionRun,
  });
}

afterEach(() => vi.unstubAllGlobals());

describe("Machine learning page", () => {
  it("asks what to predict, with the columns that cannot be predicted greyed out", async () => {
    setup();
    renderAt("/d/d1/ml");

    expect(await screen.findByRole("heading", { name: "What do you want to predict?" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /vin/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: /price.*Suggested/ })).toBeEnabled();
  });

  it("trains the reference model as soon as a target is chosen, then shows the result", async () => {
    const calls = setup();
    const router = renderAt("/d/d1/ml");

    fireEvent.click(await screen.findByRole("button", { name: /price/ }));

    expect(
      await screen.findByText("The model explains 82 % of the variation in price — 41 % better than always predicting the average."),
    ).toBeInTheDocument();
    const posted = calls.find((c) => c.key === "POST /modules/ml/datasets/d1/runs");
    expect(posted?.params.get("target")).toBe("price");
    expect(posted?.params.get("settings")).toBeNull(); // defaults resolved on the server
    await waitFor(() => expect(router.state.location.search).toMatchObject({ target: "price", run: "r1" }));
    expect(screen.getByText("1 columns → 1 model inputs · 1 excluded")).toBeInTheDocument();
  });
});

describe("ML verdicts", () => {
  const run = regressionRun as unknown as MlRun;

  it("says when a model is no better than the naive reference", () => {
    const flat = { ...run, regression: { ...run.regression!, skill: -0.2 } } as MlRun;
    expect(verdict(flat)).toContain("does no better than always predicting the average");

    const classification = {
      ...run,
      regression: null,
      classification: {
        labels: ["no", "yes"],
        positive: "yes",
        accuracy: 0.6,
        balanced_accuracy: 0.52,
        f1_macro: 0.5,
        roc_auc: 0.55,
        log_loss: 0.7,
        baseline_accuracy: 0.64,
        majority: "no",
        confusion: [],
        report: [],
        roc: null,
        pr: null,
        calibration: null,
        truth: [],
        probability: [],
      },
    } as unknown as MlRun;
    expect(verdict(classification)).toBe(
      "The model does no better than always answering “no”: the features may not carry information about the classes. (ROC AUC 0.55: 0.5 is chance.)",
    );
  });
});

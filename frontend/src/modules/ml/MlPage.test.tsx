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

describe("Preparation editor", () => {
  const size = (scaling: string, manual: string[]) => ({
    column: "size",
    type: "numeric_continuous",
    use: true,
    rules: ["R-NUM-02", "R-NUM-08"],
    why: ["Missing values → mean.", "Standardised (mean 0, standard deviation 1)."],
    impute: "mean",
    indicator: false,
    transform: null,
    encoding: null,
    scaling,
    order: null,
    auto: { use: "yes", impute: "mean", indicator: "no", transform: "none", encoding: "none", scaling: "standard" },
    manual,
    options: {
      use: [{ value: "yes", reason: null }, { value: "no", reason: null }],
      impute: [
        { value: "mean", reason: null },
        { value: "none", reason: "This model cannot handle missing values: they must be filled." },
      ],
      scaling: ["none", "standard", "robust", "minmax"].map((value) => ({ value, reason: null })),
    },
    reactivable: true,
    leak: false,
  });
  const preparation = (scaling: string, manual: string[]) => ({
    decisions: [
      { ...regressionRun.preparation.decisions[0], auto: { use: "no" }, manual: [], options: {}, reactivable: false, leak: false },
      size(scaling, manual),
      { column: "copy", type: "numeric_continuous", use: false, rules: ["R-SEL-06"], why: ["Looks like it contains the answer (association 0.999 with the target)."], impute: null, indicator: false, transform: null, encoding: null, scaling: null, order: null, auto: { use: "no" }, manual: [], options: {}, reactivable: true, leak: true },
    ],
    inputs: 1,
    excluded: 2,
    choices: { columns: {}, numeric_impute: "auto", indicator_share: 0.05, rare_share: 0.01, rare_rows: 10, one_hot_limit: 15, target_smoothing: 10, outliers: "none", imbalance: "auto", selection: [] },
    custom: manual.length > 0,
    warnings: [],
    selection: [],
    balance: null,
    dropped_rows: 0,
  });

  it("changes a column's scaling, previews it and sends it with the next training", async () => {
    const calls = mockApi({
      "GET /health": health,
      "GET /datasets": [dataset()],
      "GET /datasets/d1": dataset(),
      "GET /datasets/d1/columns": [column({ name: "price" })],
      "GET /column-roles": roles,
      "GET /modules/ml/datasets/d1/targets": { candidates: [candidate("price", "regression")], rows: 100 },
      "GET /modules/ml/catalog": [
        { key: "linear_regression", label: "Linear regression", family: "Linear models", description: "", tasks: ["regression"], settings: [] },
      ],
      "GET /modules/ml/datasets/d1/runs": [
        { id: "r1", target: "price", task: "regression", model: "linear_regression", settings: {}, metric: "r2", score: 0.82, seconds: 0.3, created_at: "2026-10-18T10:00:00Z" },
      ],
      "GET /modules/ml/datasets/d1/runs/r1": { ...regressionRun, preparation: preparation("standard", []) },
      "POST /modules/ml/datasets/d1/preparation": (body: unknown) => {
        const chosen = (body as { columns?: Record<string, { scaling?: string }> }).columns?.size?.scaling;
        return {
          preparation: preparation(chosen ?? "standard", chosen ? ["scaling"] : []),
          columns: ["size"],
          rows: [[0.5], [-1.2]],
          row_numbers: [3, 8],
          train_rows: 80,
        };
      },
      "POST /modules/ml/datasets/d1/runs": { id: "job1", status: "running", stage: "loading", run_id: null, error: null },
      "GET /modules/ml/jobs/job1": { id: "job1", status: "running", stage: "loading", run_id: null, error: null },
    });
    renderAt("/d/d1/ml?target=price");

    const edit = await screen.findByRole("button", { name: "Edit" });
    await waitFor(() => expect(edit).toBeEnabled()); // once the model is known
    fireEvent.click(edit);
    const scaling = await screen.findByRole("combobox", { name: "Scaling — size" });
    expect(scaling).toHaveValue(""); // automatic
    expect(screen.getByRole("option", { name: "Auto: Standard" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /Leave empty — This model cannot handle missing values/ })).toBeDisabled();
    expect(screen.getByText(/excluded · Looks like it contains the answer/)).toBeInTheDocument();

    fireEvent.change(scaling, { target: { value: "robust" } });
    await waitFor(() => expect(screen.getByRole("combobox", { name: "Scaling — size" })).toHaveValue("robust"));
    expect(screen.getByRole("button", { name: "Back to automatic — size" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("checkbox", { name: "Use copy" }));
    expect(screen.getByText(/seems to contain the answer/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Done" }));
    fireEvent.click(screen.getByRole("button", { name: "Train" }));
    await waitFor(() => expect(calls.some((c) => c.key === "POST /modules/ml/datasets/d1/runs")).toBe(true));
    const trained = calls.find((c) => c.key === "POST /modules/ml/datasets/d1/runs");
    expect(trained?.body).toMatchObject({ columns: { size: { scaling: "robust" } } });
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

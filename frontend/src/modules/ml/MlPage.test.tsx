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

type Model = { key: string; label: string; tasks: string[]; settings?: Record<string, unknown>[]; family?: string; rules?: unknown[]; installed?: boolean };

/** The catalogue as the API serves it. */
function catalogue(models: Model[], recommended: { key: string; why: string }[] = []) {
  return {
    families: [...new Set(models.map((m) => m.family ?? "Linear models"))],
    models: models.map((m) => ({
      family: "Linear models",
      description: `${m.label} description.`,
      rules: [],
      badges: [],
      installed: true,
      unavailable: null,
      probabilities: true,
      ...m,
      settings: (m.settings ?? []).map((s) => ({
        kind: "select",
        level: "essential",
        options: [],
        minimum: null,
        maximum: null,
        log: false,
        why: "",
        shown_when: null,
        group: "Main",
        param: "",
        option_labels: {},
        ...s,
      })),
    })),
    recommended,
    metrics: ["r2", "mae"],
    default_metric: "r2",
  };
}

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
  classes: null,
  scores: { r2: 0.82, mae: 10 },
  cross_validation: null,
  importances: [],
  validation: { method: "split", test_size: 0.2, folds: 5, repeats: 3, group: null, time_column: null, metric: null, seed: 42, max_rows: 200000 },
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
    "GET /modules/ml/catalog": catalogue([
      {
        key: "linear_regression",
        label: "Linear regression",
        tasks: ["regression"],
        settings: [{ key: "regularization", label: "Regularization", default: "none", options: ["none", "ridge", "lasso"] }],
      },
    ]),
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
      "GET /modules/ml/catalog": catalogue([{ key: "linear_regression", label: "Linear regression", tasks: ["regression"] }]),
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

describe("Predict a number as classes", () => {
  it("cuts the target live and trains a classification 600 ms after the last change", async () => {
    const values = Array.from({ length: 300 }, (_, i) => i + 1);
    const at = (level: number) => values[Math.max(0, Math.ceil(level * 300) - 1)] as number;
    const calls = mockApi({
      "GET /health": health,
      "GET /datasets": [dataset()],
      "GET /datasets/d1": dataset(),
      "GET /datasets/d1/columns": [column({ name: "price" })],
      "GET /column-roles": roles,
      "GET /modules/ml/datasets/d1/targets": { candidates: [candidate("price", "regression")], rows: 300 },
      "GET /modules/ml/catalog": catalogue([
        { key: "linear_regression", label: "Linear regression", tasks: ["regression"] },
        { key: "logistic_regression", label: "Logistic regression", tasks: ["binary", "multiclass"] },
      ]),
      "GET /modules/ml/datasets/d1/runs": [
        { id: "r1", target: "price", task: "regression", model: "linear_regression", settings: {}, metric: "r2", score: 0.82, seconds: 0.3, created_at: "2026-10-18T10:00:00Z", classes: null },
      ],
      "GET /modules/ml/datasets/d1/runs/r1": regressionRun,
      "GET /modules/ml/datasets/d1/targets/price/distribution": {
        column: "price",
        rows: 300,
        distinct: 300,
        min: 1,
        max: 300,
        p1: 3,
        p99: 297,
        quantiles: Array.from({ length: 1001 }, (_, i) => at(i / 1000)),
        equal_counts: Array.from({ length: 9 }, (_, j) => Array.from({ length: j + 1 }, (_, i) => at((i + 1) / (j + 2)))),
        histogram_start: 1,
        histogram_width: 299 / 80,
        histogram: Array.from({ length: 80 }, () => 4),
        sample: values,
        values: null,
      },
      "POST /modules/ml/datasets/d1/runs": { id: "job1", status: "running", stage: "loading", run_id: null, error: null },
      "GET /modules/ml/jobs/job1": { id: "job1", status: "running", stage: "loading", run_id: null, error: null },
    });
    renderAt("/d/d1/ml?target=price");

    fireEvent.click(await screen.findByRole("radio", { name: "Classes" }));
    expect(await screen.findByRole("textbox", { name: "Name of class 3" })).toHaveValue("High");
    expect(screen.getByText("≤ 100")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "More classes" }));
    expect(await screen.findByRole("textbox", { name: "Name of class 4" })).toHaveValue("High");

    await waitFor(() => expect(calls.some((c) => c.key === "POST /modules/ml/datasets/d1/runs")).toBe(true), { timeout: 3000 });
    const posted = calls.filter((c) => c.key === "POST /modules/ml/datasets/d1/runs");
    expect(posted).toHaveLength(1); // one training for the last setup only
    expect(JSON.parse(posted[0]?.params.get("classes") ?? "{}")).toMatchObject({
      method: "quantile",
      edges: [75, 150, 230],
      names: ["Low", "Medium-low", "Medium-high", "High"],
    });
  });
});

describe("Model catalogue", () => {
  it("picks a model by family, shows its essentials, and opens every setting in the drawer", async () => {
    const calls = mockApi({
      "GET /health": health,
      "GET /datasets": [dataset()],
      "GET /datasets/d1": dataset(),
      "GET /datasets/d1/columns": [column({ name: "price" })],
      "GET /column-roles": roles,
      "GET /modules/ml/datasets/d1/targets": { candidates: [candidate("price", "regression")], rows: 100 },
      "GET /modules/ml/catalog": catalogue(
        [
          { key: "linear_regression", label: "Linear regression", tasks: ["regression"] },
          {
            key: "random_forest",
            label: "Random forest",
            family: "Bagging ensembles",
            tasks: ["regression"],
            settings: [
              { key: "n_estimators", label: "Number of trees", kind: "int", default: 300, minimum: 10, maximum: 5000, param: "n_estimators", group: "Structure" },
              { key: "max_features", label: "Features tried per split", default: "1.0", options: ["sqrt", "1.0"], level: "advanced", group: "Sampling", param: "max_features" },
              { key: "criterion", label: "Split quality", default: "squared_error", options: ["squared_error", "absolute_error"], level: "expert", group: "Optimizer", param: "criterion" },
            ],
          },
          { key: "xgboost", label: "XGBoost", family: "Boosting ensembles", tasks: ["regression"], installed: false },
        ],
        [{ key: "random_forest", why: "Robust without tuning." }],
      ),
      "GET /modules/ml/datasets/d1/runs": [
        { id: "r1", target: "price", task: "regression", model: "linear_regression", settings: {}, metric: "r2", score: 0.82, seconds: 0.3, created_at: "2026-10-18T10:00:00Z", classes: null, greater_is_better: true },
      ],
      "GET /modules/ml/datasets/d1/runs/r1": regressionRun,
      "POST /modules/ml/datasets/d1/runs": { id: "job1", status: "running", stage: "loading", run_id: null, error: null },
      "GET /modules/ml/jobs/job1": { id: "job1", status: "running", stage: "loading", run_id: null, error: null },
    });
    renderAt("/d/d1/ml?target=price");

    fireEvent.click(await screen.findByRole("button", { name: /Linear regression.*Linear models/ }));
    expect(await screen.findByText("Recommended for this data")).toBeInTheDocument();
    expect(screen.getByText("Robust without tuning.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Boosting ensembles/ }));
    expect(screen.getByRole("button", { name: /XGBoost/ })).toBeDisabled();
    expect(screen.getByText("Not installed in this build.")).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: /Random forest/ })[0] as HTMLElement);

    const trees = await screen.findByRole("spinbutton", { name: "Number of trees" });
    expect(trees).toHaveValue(300);
    expect(screen.queryByRole("combobox", { name: "Features tried per split" })).not.toBeInTheDocument(); // advanced

    fireEvent.click(screen.getByRole("button", { name: "All settings" }));
    expect(await screen.findByRole("combobox", { name: "Features tried per split" })).toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "Optimizer" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("checkbox", { name: "Expert" }));
    fireEvent.click(screen.getByRole("tab", { name: "Optimizer" }));
    expect(screen.getByRole("combobox", { name: "Split quality" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Validation" }));
    fireEvent.change(screen.getByRole("combobox", { name: "Method" }), { target: { value: "kfold" } });
    const train = screen.getAllByRole("button", { name: "Train" });
    fireEvent.click(train[train.length - 1] as HTMLElement);

    await waitFor(() => expect(calls.some((c) => c.key === "POST /modules/ml/datasets/d1/runs")).toBe(true));
    const posted = calls.find((c) => c.key === "POST /modules/ml/datasets/d1/runs");
    expect(posted?.params.get("model")).toBe("random_forest");
    expect(JSON.parse(posted?.params.get("validation") ?? "{}")).toMatchObject({ method: "kfold", folds: 5 });
  });
});

describe("Explanations", () => {
  it("shows what the model relies on, how columns move predictions, and explains one row", async () => {
    let calls = 0;
    mockApi({
      "GET /health": health,
      "GET /datasets": [dataset()],
      "GET /datasets/d1": dataset(),
      "GET /datasets/d1/columns": [column({ name: "price" })],
      "GET /column-roles": roles,
      "GET /modules/ml/datasets/d1/targets": { candidates: [candidate("price", "regression")], rows: 100 },
      "GET /modules/ml/catalog": catalogue([{ key: "linear_regression", label: "Linear regression", tasks: ["regression"] }]),
      "GET /modules/ml/datasets/d1/runs": [
        { id: "r1", target: "price", task: "regression", model: "linear_regression", settings: {}, metric: "r2", score: 0.82, seconds: 0.3, created_at: "2026-10-18T10:00:00Z", classes: null, greater_is_better: true },
      ],
      "GET /modules/ml/datasets/d1/runs/r1": regressionRun,
      "GET /modules/ml/datasets/d1/runs/r1/explanation": () =>
        ++calls < 2
          ? { status: "running", error: null, explanation: null }
          : {
              status: "done",
              error: null,
              explanation: {
                permutation: { metric: "r2", rows: 20, sampled: false, items: [{ column: "size", mean: 0.6, std: 0.02 }] },
                shap: {
                  method: "Exact (linear model)",
                  scale: "prediction",
                  base: 100,
                  positive: null,
                  rows: [4],
                  features: [{ column: "size", mean_abs: 12, values: [15], colors: [0.9], reading: "Higher size pushes the prediction up." }],
                  columns: ["size", "city"],
                  matrix: [[15, -4]],
                  labels: [["120", "Nice"]],
                },
                shap_unavailable: null,
                dependence: [{ column: "size", kind: "number", grid: [1, 2], curves: { prediction: [90, 110] }, counts: [5, 5], output: "Average prediction" }],
                tree: null,
                pairs: [{ first: "size", second: "rooms", strength: 0.91, measure: "|r|" }],
                warnings: [],
              },
            },
    });
    renderAt("/d/d1/ml?target=price&run=r1");

    fireEvent.click(await screen.findByRole("radio", { name: "Explain" }));
    expect(await screen.findByText(/Computing the explanation/)).toBeInTheDocument();
    expect(await screen.findByText("Higher size pushes the prediction up.", {}, { timeout: 3000 })).toBeInTheDocument();
    expect(screen.getByText(/size and rooms are strongly linked/)).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Column" })).toHaveValue("size");

    fireEvent.click(screen.getByRole("radio", { name: "Predictions" }));
    fireEvent.click(screen.getByRole("button", { name: "Explain row 5" }));
    expect(await screen.findByText("Row 5: the strongest pushes come from size (+15), city (-4).")).toBeInTheDocument();
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

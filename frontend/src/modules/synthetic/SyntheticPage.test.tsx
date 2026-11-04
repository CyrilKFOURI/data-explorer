import { fireEvent, screen, within } from "@testing-library/react";
import { forwardRef } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { column, roles } from "../../test/columns";
import { dataset, health, mockApi } from "../../test/mockApi";
import { renderAt } from "../../test/render";

vi.mock("../../charts/Plot", () => ({
  Plot: forwardRef<HTMLDivElement, { label: string }>(function Plot({ label }, ref) {
    return <div ref={ref} role="img" aria-label={label} />;
  }),
}));

const planColumn = (name: string, type: string, treatment: string, rule: string, reason: string, options: string[]) => ({
  name,
  type,
  treatment,
  rule,
  reason,
  options,
  grouped: false,
});

const plan = {
  columns: [
    planColumn("customer_id", "identifier", "unique", "R-SYN-05", "New identifiers in the same format; never a real value.", ["unique", "leave"]),
    planColumn("revenue", "numeric_continuous", "model", "R-SYN-01", "Modelled; real bounds and decimals kept.", ["model", "leave"]),
    planColumn("country", "categorical_nominal", "model", "R-SYN-03", "Modelled; only existing levels are produced.", ["model", "leave"]),
    planColumn("comment", "text", "leave", "R-SYN-06", "Free text could leak real content.", ["leave"]),
    planColumn("signup", "datetime", "model", "R-SYN-04", "Modelled as a number of seconds, converted back to dates.", ["model", "leave"]),
  ],
  method: "cart",
  method_reason: "Sequential CART: best fidelity on mixed columns: keeps non-linear links.",
  methods: [
    { key: "cart", label: "Sequential CART", why: "Best fidelity on mixed columns.", available: true, unavailable: null, badge: null, epochs: null },
    { key: "copula", label: "Gaussian copula", why: "Fast; keeps monotonic links between columns.", available: true, unavailable: null, badge: null, epochs: null },
    { key: "bayes", label: "Bayesian network", why: "Suited to mostly categorical data.", available: true, unavailable: null, badge: null, epochs: null },
    { key: "independent", label: "Independent columns", why: "Reference only.", available: true, unavailable: null, badge: null, epochs: null },
    { key: "ctgan", label: "CTGAN", why: "Neural network (GAN).", available: false, unavailable: "Needs the deep extra (PyTorch): uv sync --extra deep.", badge: "Deep · GPU", epochs: 300 },
    { key: "tvae", label: "TVAE", why: "Neural network (autoencoder).", available: true, unavailable: null, badge: "Deep · GPU", epochs: 300 },
    { key: "timegan", label: "TimeGAN", why: "Neural network for sequences.", available: true, unavailable: null, badge: "Deep · GPU", epochs: 1000 },
  ],
  rows: 1200,
  default_rows: 1200,
  train_rows: 960,
  modelled: 2,
  error: null,
  smooth: true,
  smooth_reason: "On: continuous numbers stay off the real values.",
  gpu: "NVIDIA GeForce RTX 4050 Laptop GPU",
  sequence: {
    time: "signup",
    entity: "country",
    candidates: [{ name: "country", sequences: 3, median_length: 400, reason: "3 histories of about 400 dates, one value per date." }],
    step_seconds: 86400,
    step: "daily",
    length: 24,
    sequences: 3,
    reason: "One sequence per country, 24 steps each.",
    error: null,
  },
};

const learned = (name: string, kind: string, levels: string[] = []) => ({
  name,
  type: kind === "category" ? "categorical_nominal" : "numeric_continuous",
  kind,
  missing: 0,
  minimum: null,
  maximum: null,
  decimals: 2,
  day_only: false,
  levels,
  grouped: false,
});

const run = {
  id: "r1",
  dataset_id: "d1",
  created_at: "2026-10-19T10:00:00Z",
  method: "cart",
  method_label: "Sequential CART",
  settings: { method: "cart", rows: 1200, seed: 42, smooth: true, drop_copies: true, treatments: {}, bounds: {} },
  rows: 1200,
  seconds: 2.4,
  train_rows: 960,
  holdout_rows: 240,
  columns: [],
  created_dataset_id: null,
  report: {
    scores: { diagnostic: 1, quality: 0.93, shapes: 0.95, trends: 0.91, detection: 0.88, privacy: 0.97, utility: null },
    verdicts: { diagnostic: "All values valid", quality: "Very close", detection: "Hard to tell apart", privacy: "No copied rows" },
    header: { real_rows: 960, holdout_rows: 240, synthetic_rows: 1200, real_duplicates: 0, synthetic_duplicates: 0, types: {}, left_out: [{ column: "comment", reason: "Free text could leak real content." }] },
    diagnostic: { score: 1, validity: 1, structure: 1, checks: [], failures: [] },
    quality: { score: 0.93, shapes: 0.95, trends: 0.91, shape_scores: [], pair_scores: [], coverage: [] },
    detection: { score: 0.88, detectors: [], giveaways: [], rows: 960 },
    privacy: {
      score: 0.97,
      unique_copies: 0,
      unique_copy_share: 0,
      copies: 0,
      copy_share: 0,
      near_copies: 12,
      new_rows: 0.99,
      overfitting: 0.97,
      closer_to_train: 0.51,
      baseline: 0.6,
      median_dcr: 0.08,
      rare: [],
      histogram: null,
      warnings: [],
      verdict: "No unique real row copied, and synthetic rows are no closer to the real ones than new real rows would be.",
    },
    columns: [
      { column: "country", type: "categorical_nominal", kind: "category", metric: "TV", score: 0.9, real: [0.6, 0.4], synthetic: [0.5, 0.5], biggest: "'FR' 60 % → 50 %" },
      { column: "revenue", type: "numeric_continuous", kind: "number", metric: "KS", score: 0.97, real: [0.5, 0.5], synthetic: [0.5, 0.5], biggest: "mean +2 %" },
    ],
    links: { columns: ["revenue", "country"], real: [[1, 0.4], [0.4, 1]], synthetic: [[1, 0.35], [0.35, 1]], gap: [[0, 0.05], [0.05, 0]], measures: [["", "eta"], ["eta", ""]], worst: [] },
    overview: { mean_spread: [], pca: null },
    fitted: { method: "cart", order: ["country", "revenue"], edges: [], notes: [], dropped: 0 },
    learned: [learned("revenue", "number"), learned("country", "category", ["FR", "DE"])],
    utility: null,
    disclosure: null,
  },
};

const countryDetail = {
  column: "country",
  type: "categorical_nominal",
  kind: "category",
  score: 0.9,
  counts: [{ label: "Values", real: 960, real_share: 1, synthetic: 1200, synthetic_share: 1 }],
  histogram: null,
  ecdf: null,
  stats: [],
  frequent_real: [],
  frequent_synthetic: [],
  smallest: [],
  largest: [],
  levels: [
    { value: "FR", real: 576, real_share: 0.6, synthetic: 600, synthetic_share: 0.5, delta: -0.1, status: null },
    { value: "DE", real: 384, real_share: 0.4, synthetic: 600, synthetic_share: 0.5, delta: 0.1, status: null },
  ],
  target: null,
};

function setup(runs: unknown[] = []) {
  return mockApi({
    "GET /health": health,
    "GET /datasets": [dataset()],
    "GET /datasets/d1": dataset(),
    "GET /datasets/d1/columns": [column({ name: "revenue" })],
    "GET /column-roles": roles,
    "GET /modules/synthetic/datasets/d1/plan": plan,
    "GET /modules/synthetic/datasets/d1/runs": runs,
    "POST /modules/synthetic/datasets/d1/runs": { id: "job1", status: "running", stage: "loading", run_id: null, error: null },
    "GET /modules/synthetic/jobs/job1": { id: "job1", status: "done", stage: "saving", run_id: "r1", error: null },
    "GET /modules/synthetic/datasets/d1/runs/r1": run,
    "GET /modules/synthetic/datasets/d1/runs/r1/columns/country": countryDetail,
  });
}

afterEach(() => vi.unstubAllGlobals());

describe("Synthetic data page", () => {
  it("opens ready to generate: every column with its treatment, rule and reason", async () => {
    setup();
    renderAt("/d/d1/synthetic");

    expect(await screen.findByRole("heading", { name: "Synthetic data" })).toBeInTheDocument();
    const table = await screen.findByRole("table", { name: "Columns" });
    expect(within(table).getByText("R-SYN-05")).toBeInTheDocument();
    expect(within(table).getByText("Free text could leak real content.")).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Method" })).toHaveValue("cart");
    expect(screen.getByText("3 of 5 columns modelled")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Generate" })).toBeEnabled();
  });

  it("generates with the user's changes, then shows the four figures and the columns", async () => {
    const calls = setup();
    renderAt("/d/d1/synthetic");

    fireEvent.change(await screen.findByRole("combobox", { name: "Treatment of country" }), { target: { value: "leave" } });
    expect(screen.getByText("2 of 5 columns modelled")).toBeInTheDocument();
    fireEvent.change(screen.getByRole("combobox", { name: "Treatment of customer_id" }), { target: { value: "leave" } });
    fireEvent.click(screen.getByRole("button", { name: "Generate" }));

    expect(await screen.findByText("Very close")).toBeInTheDocument();
    const posted = calls.find((c) => c.key === "POST /modules/synthetic/datasets/d1/runs");
    expect(posted?.body).toMatchObject({ method: "cart", rows: 1200, seed: 42, smooth: true, treatments: { country: "leave", customer_id: "leave" } });
    expect(screen.getByText("93 %")).toBeInTheDocument();
    expect(screen.getByText("Hard to tell apart")).toBeInTheDocument();
    expect(screen.getByText("'FR' 60 % → 50 %")).toBeInTheDocument();
    // the most damaged column opens first, real and synthetic side by side
    expect(await screen.findByRole("table", { name: "Levels, aligned" })).toBeInTheDocument();
  });

  it("offers the deep models with their epochs and the GPU, greyed out when PyTorch is missing", async () => {
    const calls = setup();
    renderAt("/d/d1/synthetic");

    const method = await screen.findByRole("combobox", { name: "Method" });
    expect(within(method).getByRole("option", { name: /CTGAN · needs PyTorch/ })).toBeDisabled();
    fireEvent.change(method, { target: { value: "tvae" } });
    expect(screen.getByRole("spinbutton", { name: "Epochs" })).toHaveAttribute("placeholder", "Auto (300)");
    const pill = screen.getByRole("button", { name: "GPU · RTX 4050" });
    fireEvent.click(pill);
    expect(screen.getByRole("button", { name: "CPU" })).toHaveAttribute("aria-pressed", "false");
    fireEvent.click(screen.getByRole("button", { name: "Generate" }));
    await screen.findByText("Very close");
    const posted = calls.find((c) => c.key === "POST /modules/synthetic/datasets/d1/runs");
    expect(posted?.body).toMatchObject({ method: "tvae", device: "cpu", epochs: null });
  });

  it("sets up TimeGAN's sequences and shows how their dynamics compare", async () => {
    const calls = setup();
    renderAt("/d/d1/synthetic");

    fireEvent.change(await screen.findByRole("combobox", { name: "Method" }), { target: { value: "timegan" } });
    expect(screen.getByRole("combobox", { name: "Entity" })).toHaveValue("country");
    expect(screen.getByText("= 72 rows")).toBeInTheDocument();
    expect(screen.queryByRole("spinbutton", { name: "Rows" })).not.toBeInTheDocument();
    expect(document.body).toHaveTextContent("Neural network for sequences. One sequence per country, 24 steps each. · daily");
    fireEvent.change(screen.getByRole("spinbutton", { name: "Length" }), { target: { value: "12" } });
    fireEvent.click(screen.getByRole("button", { name: "Generate" }));
    await screen.findByText("Very close");
    const posted = calls.find((c) => c.key === "POST /modules/synthetic/datasets/d1/runs");
    expect(posted?.body).toMatchObject({ method: "timegan", sequence: { length: 12 }, epochs: null });
  });

  it("reopens the latest run and says where its privacy stands", async () => {
    setup([{ id: "r1", method: "cart", method_label: "Sequential CART", rows: 1200, seconds: 2.4, created_at: run.created_at, scores: run.report.scores, created_dataset_id: null, settings: run.settings }]);
    renderAt("/d/d1/synthetic?tab=privacy");

    expect(await screen.findByText(/No unique real row copied, and synthetic rows/)).toBeInTheDocument();
    expect(screen.getByText("Copies of unique real rows")).toBeInTheDocument();
    expect(screen.getByText(/not a differential-privacy guarantee/)).toBeInTheDocument();
  });
});

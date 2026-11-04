import { describe, expect, it } from "vitest";

import type { MlModel } from "../../api/client";
import { disabledOptions, isVisible, resolveValues } from "./rules";

const setting = (key: string, extra: Record<string, unknown>) => ({
  key,
  label: key,
  kind: "select",
  default: null,
  level: "essential",
  options: [],
  minimum: null,
  maximum: null,
  log: false,
  why: "",
  shown_when: null,
  group: "Main",
  param: key,
  option_labels: {},
  ...extra,
});

const logistic = {
  key: "logistic_regression",
  label: "Logistic regression",
  family: "Linear models",
  description: "",
  tasks: ["binary"],
  badges: [],
  installed: true,
  unavailable: null,
  probabilities: true,
  settings: [
    setting("penalty", { default: "l2", options: ["l2", "l1", "elasticnet"] }),
    setting("solver", { default: "lbfgs", options: ["lbfgs", "liblinear", "saga"] }),
    setting("l1_ratio", { kind: "number", default: 0.5, shown_when: { penalty: ["elasticnet"] } }),
  ],
  rules: [{ when: { penalty: ["l1"] }, setting: "solver", allowed: ["saga", "liblinear"], reason: "L1 penalty needs the liblinear or saga solver." }],
} as unknown as MlModel;

describe("catalogue rules in the browser", () => {
  it("only offers the solvers an L1 penalty allows, with the reason", () => {
    const disabled = disabledOptions(logistic, { penalty: "l1", solver: "saga" });
    expect(disabled.solver).toEqual({ lbfgs: "L1 penalty needs the liblinear or saga solver." });
    expect(disabledOptions(logistic, { penalty: "l2", solver: "lbfgs" })).toEqual({});
  });

  it("moves a default to an allowed value but reports a choice that breaks a rule", () => {
    expect(resolveValues(logistic, {}, { penalty: "l1" }).values.solver).toBe("saga");
    const broken = resolveValues(logistic, {}, { penalty: "l1", solver: "lbfgs" });
    expect(broken.error).toBe("L1 penalty needs the liblinear or saga solver.");
  });

  it("hides a setting without effect", () => {
    const ratio = logistic.settings[2]!;
    expect(isVisible(ratio, { penalty: "l2" })).toBe(false);
    expect(isVisible(ratio, { penalty: "elasticnet" })).toBe(true);
  });
});

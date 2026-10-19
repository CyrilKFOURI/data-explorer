/** The catalogue's declarations applied in the browser, exactly as the server applies them
 *  (019): which settings show, which options a rule disables, and which value a rule forces. */

import type { MlModel, MlSetting } from "../../api/client";

export type Values = Record<string, unknown>;

const same = (a: unknown, b: unknown) => a === b || String(a) === String(b);

export function isVisible(setting: MlSetting, values: Values): boolean {
  if (!setting.shown_when) return true;
  return Object.entries(setting.shown_when).every(([key, allowed]) => allowed.some((a) => same(a, values[key])));
}

function matches(when: Record<string, unknown[]>, values: Values): boolean {
  return Object.entries(when).every(([key, allowed]) => allowed.some((a) => same(a, values[key])));
}

/** Options a rule disables right now, with its reason: { setting: { option: reason } }. */
export function disabledOptions(model: MlModel, values: Values): Record<string, Record<string, string>> {
  const found: Record<string, Record<string, string>> = {};
  for (const rule of model.rules) {
    if (!matches(rule.when, values)) continue;
    const setting = model.settings.find((s) => s.key === rule.setting);
    for (const option of setting?.options ?? []) {
      if (!rule.allowed.some((a) => same(a, option))) (found[rule.setting] ??= {})[option] = rule.reason;
    }
    if (setting?.kind === "bool")
      for (const option of [true, false])
        if (!rule.allowed.some((a) => same(a, option))) (found[rule.setting] ??= {})[String(option)] = rule.reason;
  }
  return found;
}

/** Defaults overridden by the user's values, then the rules: a default that breaks a rule takes
 *  the first allowed value; a value the user chose that breaks one is reported. */
export function resolveValues(model: MlModel, defaults: Values, chosen: Values): { values: Values; error: string | null } {
  const values: Values = {};
  for (const s of model.settings) values[s.key] = s.key in chosen ? chosen[s.key] : (defaults[s.key] ?? s.default);
  let error: string | null = null;
  for (const rule of model.rules) {
    if (!matches(rule.when, values) || rule.allowed.some((a) => same(a, values[rule.setting]))) continue;
    if (rule.setting in chosen) error ??= rule.reason;
    else values[rule.setting] = rule.allowed[0];
  }
  return { values, error };
}

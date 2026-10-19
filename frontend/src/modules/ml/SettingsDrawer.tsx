import * as RadixDialog from "@radix-ui/react-dialog";
import { RotateCcw, X } from "lucide-react";
import { useState, type ReactNode } from "react";

import type { MlCandidate, MlModel, MlSetting, MlValidation } from "../../api/client";
import { t, type MessageKey } from "../../lib/i18n";
import { Button } from "../../ui/Button";
import { Checkbox, Select, TextInput } from "../../ui/fields";
import { InfoTip } from "../../ui/InfoTip";
import { Tabs } from "../../ui/Tabs";
import { disabledOptions, isVisible, type Values } from "./rules";

export const DEFAULT_VALIDATION: MlValidation = {
  method: "split",
  test_size: 0.2,
  folds: 5,
  repeats: 3,
  group: null,
  time_column: null,
  metric: null,
  seed: 42,
  max_rows: 200_000,
};

export const metricName = (metric: string) => t(`ml.metric.${metric}` as MessageKey);

/** One setting: plain label, its field, why the default, the library's name; a dot and a reset
 *  button once changed; options a rule forbids are disabled with the reason. */
export function SettingField({
  setting,
  value,
  changed,
  disabled,
  onChange,
  onReset,
  technical = false,
}: {
  setting: MlSetting;
  value: unknown;
  changed: boolean;
  disabled?: Record<string, string>;
  onChange: (value: unknown) => void;
  onReset: () => void;
  technical?: boolean;
}) {
  const label = (
    <span className="flex min-w-0 items-center gap-1 text-xs text-ink-2">
      {changed && <span className="size-1.5 shrink-0 rounded-full bg-accent" aria-hidden />}
      <span className="truncate">{setting.label}</span>
      {setting.why && <InfoTip label={setting.label} text={setting.why} />}
    </span>
  );
  let field: ReactNode;
  if (setting.kind === "select") {
    field = (
      <Select aria-label={setting.label} value={String(value)} onChange={(event) => onChange(event.target.value)} className="h-7 max-w-44 text-xs">
        {setting.options.map((option) => {
          const reason = disabled?.[option];
          const name = setting.option_labels[option] ?? option;
          return (
            <option key={option} value={option} disabled={Boolean(reason)}>
              {reason ? `${name} — ${reason}` : name}
            </option>
          );
        })}
      </Select>
    );
  } else if (setting.kind === "bool") {
    const reason = disabled?.[String(!value)];
    field = <Checkbox aria-label={setting.label} checked={Boolean(value)} disabled={Boolean(reason)} title={reason} onChange={(event) => onChange(event.target.checked)} />;
  } else if (setting.kind === "text") {
    field = (
      <TextInput key={String(value)} aria-label={setting.label} defaultValue={String(value)} onBlur={(event) => onChange(event.target.value)} className="h-7 w-28 text-xs" />
    );
  } else {
    field = (
      <TextInput
        key={String(value)}
        aria-label={setting.label}
        type="number"
        defaultValue={String(value)}
        min={setting.minimum ?? undefined}
        max={setting.maximum ?? undefined}
        step={setting.kind === "int" ? 1 : "any"}
        onBlur={(event) => event.target.value !== "" && onChange(Number(event.target.value))}
        onKeyDown={(event) => event.key === "Enter" && event.currentTarget.blur()}
        className="h-7 w-24 text-xs"
      />
    );
  }
  return (
    <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-3 gap-y-0.5">
      {label}
      <span className="flex items-center gap-1">
        {field}
        {changed && (
          <button type="button" onClick={onReset} aria-label={t("ml.settings.resetOne", { setting: setting.label })} className="inline-flex size-5 items-center justify-center rounded text-ink-3 hover:bg-surface-2 hover:text-ink-1">
            <RotateCcw size={12} strokeWidth={1.5} aria-hidden />
          </button>
        )}
      </span>
      {technical && setting.param && <span className="col-span-2 font-mono text-[10px] text-ink-3">{setting.param}</span>}
    </div>
  );
}

type Tab = "model" | "optimizer" | "validation" | "rows";

export function SettingsDrawer({
  open,
  onOpenChange,
  model,
  values,
  chosen,
  onChange,
  onReset,
  validation,
  onValidation,
  metrics,
  candidates,
  task,
  onPreparation,
  onTrain,
  training,
  error,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  model: MlModel;
  values: Values;
  chosen: Values;
  onChange: (key: string, value: unknown) => void;
  onReset: (key?: string) => void;
  validation: MlValidation;
  onValidation: (next: MlValidation) => void;
  metrics: string[];
  candidates: MlCandidate[];
  task: string;
  onPreparation: () => void;
  onTrain: () => void;
  training: boolean;
  error: string | null;
}) {
  const [tab, setTab] = useState<Tab>("model");
  const [expert, setExpert] = useState(false);
  const disabled = disabledOptions(model, values);
  const shown = (s: MlSetting) => isVisible(s, values) && (expert || s.level !== "expert");
  const modelSettings = model.settings.filter((s) => s.group !== "Optimizer" && shown(s));
  const optimizer = model.settings.filter((s) => s.group === "Optimizer" && shown(s));
  const groups = [...new Set(modelSettings.map((s) => s.group))];
  const active = tab === "optimizer" && !expert ? "model" : tab;
  const field = (s: MlSetting) => (
    <SettingField
      key={s.key}
      setting={s}
      value={values[s.key]}
      changed={s.key in chosen}
      disabled={disabled[s.key]}
      onChange={(value) => onChange(s.key, value)}
      onReset={() => onReset(s.key)}
      technical
    />
  );
  return (
    <RadixDialog.Root open={open} onOpenChange={onOpenChange}>
      <RadixDialog.Portal>
        <RadixDialog.Overlay className="fixed inset-0 z-40 bg-ink-1/20" />
        <RadixDialog.Content className="fixed top-0 right-0 bottom-0 z-50 flex w-[min(480px,100vw)] flex-col border-l border-line bg-surface-1 shadow-[0_12px_40px_-12px_rgb(0_0_0/0.35)]">
          <header className="flex items-center justify-between gap-3 border-b border-line px-5 py-3">
            <div className="min-w-0">
              <RadixDialog.Title className="truncate text-sm font-semibold">{t("ml.settings.title", { model: model.label })}</RadixDialog.Title>
              <RadixDialog.Description className="text-xs text-ink-3">{t("ml.settings.description")}</RadixDialog.Description>
            </div>
            <span className="flex items-center gap-2">
              <Checkbox className="text-xs text-ink-2" label={t("ml.settings.expert")} checked={expert} onChange={(e) => setExpert(e.target.checked)} />
              <Button variant="ghost" onClick={() => onReset()} disabled={Object.keys(chosen).length === 0}>
                {t("ml.settings.resetAll")}
              </Button>
              <RadixDialog.Close aria-label={t("dialog.close")} className="inline-flex size-7 items-center justify-center rounded-md text-ink-3 hover:bg-surface-2 hover:text-ink-1">
                <X size={16} strokeWidth={1.5} aria-hidden />
              </RadixDialog.Close>
            </span>
          </header>
          <div className="min-h-0 flex-1 overflow-y-auto px-5 py-3">
            <Tabs
              label={t("ml.settings.title", { model: model.label })}
              value={active}
              onChange={setTab}
              items={[
                { value: "model", label: t("ml.settings.tab.model") },
                ...(expert ? [{ value: "optimizer" as const, label: t("ml.settings.tab.optimizer") }] : []),
                { value: "validation", label: t("ml.settings.tab.validation") },
                { value: "rows", label: t("ml.settings.tab.rows") },
              ]}
            >
              {active === "model" && (
                <div className="space-y-4">
                  {groups.map((group) => (
                    <section key={group} className="space-y-2.5">
                      <h3 className="text-[11px] font-medium tracking-wide text-ink-3 uppercase">{group}</h3>
                      {modelSettings.filter((s) => s.group === group).map(field)}
                    </section>
                  ))}
                  <section className="space-y-1 border-t border-line pt-3">
                    <h3 className="text-[11px] font-medium tracking-wide text-ink-3 uppercase">{t("ml.preparation")}</h3>
                    <Button variant="ghost" onClick={onPreparation}>
                      {t("ml.settings.openPreparation")}
                    </Button>
                  </section>
                </div>
              )}
              {active === "optimizer" && (
                <div className="space-y-2.5">
                  {optimizer.length ? optimizer.map(field) : <p className="text-xs text-ink-3">{t("ml.settings.noOptimizer")}</p>}
                </div>
              )}
              {active === "validation" && <ValidationTab validation={validation} onValidation={onValidation} metrics={metrics} candidates={candidates} task={task} />}
              {active === "rows" && <RowsTab validation={validation} onValidation={onValidation} />}
            </Tabs>
          </div>
          <footer className="flex items-center gap-3 border-t border-line px-5 py-3">
            {error && <span className="flex-1 text-xs text-bad">{error}</span>}
            <Button variant="primary" className="ml-auto" onClick={onTrain} disabled={training || Boolean(error)}>
              {t("ml.train")}
            </Button>
          </footer>
        </RadixDialog.Content>
      </RadixDialog.Portal>
    </RadixDialog.Root>
  );
}

function Row({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <label className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-3 gap-y-0.5 text-xs">
      <span className="text-ink-2">{label}</span>
      {children}
      {hint && <span className="col-span-2 text-[11px] text-ink-3">{hint}</span>}
    </label>
  );
}

function NumberBox({ value, min, max, step = 1, label, onChange }: { value: number; min: number; max: number; step?: number; label: string; onChange: (v: number) => void }) {
  return (
    <TextInput
      key={value}
      aria-label={label}
      type="number"
      min={min}
      max={max}
      step={step}
      defaultValue={value}
      onBlur={(e) => {
        const next = Number(e.target.value);
        if (Number.isFinite(next)) onChange(Math.min(max, Math.max(min, next)));
      }}
      className="h-7 w-24 text-xs"
    />
  );
}

const METHODS = ["split", "kfold", "repeated_kfold", "group_kfold", "time_split", "loo"] as const;

function ValidationTab({
  validation,
  onValidation,
  metrics,
  candidates,
  task,
}: {
  validation: MlValidation;
  onValidation: (next: MlValidation) => void;
  metrics: string[];
  candidates: MlCandidate[];
  task: string;
}) {
  const set = (patch: Partial<MlValidation>) => onValidation({ ...validation, ...patch });
  const dates = candidates.filter((c) => c.type === "datetime");
  const method = validation.method;
  return (
    <div className="space-y-3">
      <Row label={t("ml.validation.method")} hint={t(`ml.validation.methodHint.${method}` as MessageKey)}>
        <Select aria-label={t("ml.validation.method")} value={method} onChange={(e) => set({ method: e.target.value as MlValidation["method"] })} className="h-7 max-w-48 text-xs">
          {METHODS.map((m) => (
            <option key={m} value={m} disabled={m === "time_split" && dates.length === 0}>
              {t(`ml.validation.method.${m}` as MessageKey)}
            </option>
          ))}
        </Select>
      </Row>
      {(method === "split" || method === "time_split") && (
        <Row label={t("ml.validation.testSize")}>
          <NumberBox label={t("ml.validation.testSize")} value={Math.round(validation.test_size * 100)} min={10} max={40} onChange={(v) => set({ test_size: v / 100 })} />
        </Row>
      )}
      {(method === "kfold" || method === "repeated_kfold" || method === "group_kfold") && (
        <Row label={t("ml.validation.folds")}>
          <NumberBox label={t("ml.validation.folds")} value={validation.folds} min={3} max={10} onChange={(v) => set({ folds: v })} />
        </Row>
      )}
      {method === "repeated_kfold" && (
        <Row label={t("ml.validation.repeats")}>
          <NumberBox label={t("ml.validation.repeats")} value={validation.repeats} min={2} max={10} onChange={(v) => set({ repeats: v })} />
        </Row>
      )}
      {method === "group_kfold" && (
        <Row label={t("ml.validation.group")} hint={t("ml.validation.groupHint")}>
          <Select aria-label={t("ml.validation.group")} value={validation.group ?? ""} onChange={(e) => set({ group: e.target.value || null })} className="h-7 max-w-44 text-xs">
            <option value="">—</option>
            {candidates.map((c) => (
              <option key={c.name} value={c.name}>
                {c.name}
              </option>
            ))}
          </Select>
        </Row>
      )}
      {method === "time_split" && (
        <Row label={t("ml.validation.timeColumn")}>
          <Select aria-label={t("ml.validation.timeColumn")} value={validation.time_column ?? ""} onChange={(e) => set({ time_column: e.target.value || null })} className="h-7 max-w-44 text-xs">
            <option value="">—</option>
            {dates.map((c) => (
              <option key={c.name} value={c.name}>
                {c.name}
              </option>
            ))}
          </Select>
        </Row>
      )}
      <Row label={t("ml.validation.metric")} hint={t(task === "regression" ? "ml.validation.metricHintRegression" : "ml.validation.metricHintClasses")}>
        <Select aria-label={t("ml.validation.metric")} value={validation.metric ?? ""} onChange={(e) => set({ metric: e.target.value || null })} className="h-7 max-w-44 text-xs">
          <option value="">{t("ml.validation.metricAuto", { metric: metricName(metrics[0] ?? "") })}</option>
          {metrics.map((m) => (
            <option key={m} value={m}>
              {metricName(m)}
            </option>
          ))}
        </Select>
      </Row>
      <Row label={t("ml.validation.seed")}>
        <NumberBox label={t("ml.validation.seed")} value={validation.seed} min={0} max={2 ** 31 - 1} onChange={(v) => set({ seed: Math.round(v) })} />
      </Row>
    </div>
  );
}

function RowsTab({ validation, onValidation }: { validation: MlValidation; onValidation: (next: MlValidation) => void }) {
  const mode = validation.max_rows === null ? "all" : validation.max_rows === 200_000 ? "default" : "fixed";
  return (
    <div className="space-y-3">
      <Row label={t("ml.rows.training")} hint={t("ml.rows.hint")}>
        <Select
          aria-label={t("ml.rows.training")}
          value={mode}
          onChange={(e) => onValidation({ ...validation, max_rows: e.target.value === "all" ? null : e.target.value === "default" ? 200_000 : 50_000 })}
          className="h-7 text-xs"
        >
          <option value="default">{t("ml.rows.default")}</option>
          <option value="all">{t("ml.rows.all")}</option>
          <option value="fixed">{t("ml.rows.fixed")}</option>
        </Select>
      </Row>
      {mode === "fixed" && validation.max_rows !== null && (
        <Row label={t("ml.rows.count")}>
          <NumberBox label={t("ml.rows.count")} value={validation.max_rows} min={100} max={100_000_000} onChange={(v) => onValidation({ ...validation, max_rows: Math.round(v) })} />
        </Row>
      )}
    </div>
  );
}

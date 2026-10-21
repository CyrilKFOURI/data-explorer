import { Check, KeyRound } from "lucide-react";
import { useState } from "react";

import { t } from "../../lib/i18n";
import { Button } from "../../ui/Button";
import { ErrorNote, Field, Select, TextInput } from "../../ui/fields";
import type { AgentSettings } from "./api";
import { useTestAgentKey, useUpdateAgentSettings } from "./useAgent";

const MODEL_LABELS: Record<string, string> = {
  "claude-opus-5-5": "Claude Opus 5.5 — most capable",
  "claude-sonnet-5-5": "Claude Sonnet 5.5 — faster, half the price",
  "claude-haiku-5-5": "Claude Haiku 5.5 — quickest, cheapest",
};
const EFFORTS = ["low", "medium", "high", "xhigh", "max"] as const;

/** Key, model, effort and budget of the assistant (spec 026 § 9). */
export function SettingsView({ settings, onDone }: { settings: AgentSettings; onDone: () => void }) {
  const update = useUpdateAgentSettings();
  const test = useTestAgentKey();
  const [key, setKey] = useState("");
  const [budget, setBudget] = useState(String(settings.budget_usd));

  const saveKey = () => {
    update.mutate({ api_key: key }, { onSuccess: () => setKey("") });
  };

  return (
    <div className="space-y-5 p-4 text-[13px]">
      {!settings.sdk_installed && <ErrorNote>{t("agent.sdkMissing")}</ErrorNote>}

      <section className="space-y-2">
        <h3 className="flex items-center gap-1.5 font-medium text-ink-1">
          <KeyRound size={14} aria-hidden />
          {t("agent.key")}
        </h3>
        <p className="text-xs text-ink-3">
          {settings.key.configured
            ? t(settings.key.source === "env" ? "agent.keyFromEnv" : "agent.keySaved", { hint: settings.key.hint ?? "" })
            : t("agent.keyNone")}
        </p>
        {settings.key.source !== "env" && (
          <div className="flex gap-2">
            <TextInput
              type="password"
              autoComplete="off"
              placeholder="sk-ant-…"
              aria-label={t("agent.key")}
              value={key}
              onChange={(event) => setKey(event.target.value)}
              className="min-w-0 flex-1"
            />
            <Button onClick={saveKey} disabled={!key.trim() || update.isPending}>
              {t("agent.save")}
            </Button>
          </div>
        )}
        <div className="flex flex-wrap items-center gap-2">
          <Button onClick={() => test.mutate()} disabled={!settings.key.configured || test.isPending}>
            {test.isPending ? t("agent.testing") : t("agent.test")}
          </Button>
          {settings.key.source === "file" && (
            <Button variant="ghost" onClick={() => update.mutate({ api_key: "" })}>
              {t("agent.removeKey")}
            </Button>
          )}
          {test.isSuccess && (
            <span className="inline-flex items-center gap-1 text-xs text-ok">
              <Check size={13} aria-hidden />
              {t("agent.keyWorks", { model: test.data.model })}
            </span>
          )}
        </div>
        {test.isError && <ErrorNote>{test.error.message}</ErrorNote>}
        <p className="text-xs text-ink-3">{t("agent.privacy")}</p>
      </section>

      <section className="space-y-3">
        <Field label={t("agent.model")}>
          <Select value={settings.model} onChange={(event) => update.mutate({ model: event.target.value })}>
            {settings.models.map((model) => (
              <option key={model} value={model}>
                {MODEL_LABELS[model] ?? model}
              </option>
            ))}
          </Select>
        </Field>
        <Field label={t("agent.effort")}>
          <Select
            value={settings.effort}
            onChange={(event) => update.mutate({ effort: event.target.value as (typeof EFFORTS)[number] })}
          >
            {EFFORTS.map((effort) => (
              <option key={effort} value={effort}>
                {effort}
              </option>
            ))}
          </Select>
        </Field>
        <p className="-mt-1 text-xs text-ink-3">{t("agent.effortHint")}</p>
        <Field label={t("agent.budget")}>
          <TextInput
            type="number"
            min={0.05}
            max={100}
            step={0.05}
            value={budget}
            onChange={(event) => setBudget(event.target.value)}
            onBlur={() => {
              const value = Number(budget);
              if (value > 0 && value <= 100 && value !== settings.budget_usd) update.mutate({ budget_usd: value });
            }}
          />
        </Field>
        <p className="-mt-1 text-xs text-ink-3">{t("agent.budgetHint")}</p>
      </section>
      {update.isError && <ErrorNote>{update.error.message}</ErrorNote>}

      <Button variant="primary" onClick={onDone}>
        {t("agent.backToChat")}
      </Button>
    </div>
  );
}

import { useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams, useSearch } from "@tanstack/react-router";
import { Search } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import type { MlCandidate, MlChoicesInput, MlRun, MlSetting } from "../../api/client";
import { useDataset, useMlCatalog, useMlJob, useMlRun, useMlRuns, useMlTargets, useMlTrain } from "../../api/hooks";
import { formatNumber } from "../../charts/figures";
import { t, type MessageKey } from "../../lib/i18n";
import { Button } from "../../ui/Button";
import { ErrorNote, Select, TextInput } from "../../ui/fields";
import { InfoTip } from "../../ui/InfoTip";
import { PreparationEditor, preparationSummary } from "./PreparationEditor";
import { Results } from "./Results";

export type MlSearch = { target?: string; run?: string };

export function validateMlSearch(search: Record<string, unknown>): MlSearch {
  const text = (value: unknown) => (typeof value === "string" && value ? value : undefined);
  return { target: text(search.target), run: text(search.run) };
}

const taskName = (task: string) => t(`ml.task.${task}` as MessageKey);

export function MlPage() {
  const { datasetId } = useParams({ strict: false }) as { datasetId: string };
  const search = useSearch({ strict: false }) as MlSearch;
  const navigate = useNavigate();
  const set = (patch: MlSearch) =>
    void navigate({ to: ".", search: (previous: Record<string, unknown>) => ({ ...previous, ...patch }), replace: true });
  const dataset = useDataset(datasetId);
  const ready = dataset.data?.status === "ready";
  const targets = useMlTargets(datasetId, ready);
  const candidate = targets.data?.candidates.find((c) => c.name === search.target && c.task);

  return (
    <div className="flex flex-col gap-5 px-8 py-6">
      <header className="max-w-prose">
        <h1 className="text-xl font-semibold tracking-tight">{t("ml.title")}</h1>
        <p className="mt-1 text-ink-2">{t("ml.description")}</p>
      </header>
      {targets.isError ? (
        <ErrorNote>{targets.error.message}</ErrorNote>
      ) : !targets.data ? (
        <div className="h-72 animate-pulse rounded-lg bg-surface-1" aria-busy="true" />
      ) : !candidate ? (
        <TargetPicker candidates={targets.data.candidates} onPick={(name) => set({ target: name, run: undefined })} />
      ) : (
        <Workbench
          key={candidate.name}
          datasetId={datasetId}
          candidate={candidate}
          candidates={targets.data.candidates}
          rows={targets.data.rows}
          runId={search.run}
          onTarget={(name) => set({ target: name, run: undefined })}
          onRun={(run) => set({ run })}
        />
      )}
    </div>
  );
}

function TargetPicker({ candidates, onPick }: { candidates: MlCandidate[]; onPick: (name: string) => void }) {
  const [query, setQuery] = useState("");
  const needle = query.trim().toLowerCase();
  const shown = candidates.filter((c) => !needle || c.name.toLowerCase().includes(needle));
  return (
    <section className="mx-auto w-full max-w-2xl space-y-3 rounded-lg border border-line bg-surface-1 p-5" aria-labelledby="ml-question">
      <h2 id="ml-question" className="text-lg font-semibold tracking-tight">
        {t("ml.question")}
      </h2>
      <p className="text-[13px] text-ink-2">{t("ml.questionHint")}</p>
      <div className="relative">
        <Search size={14} strokeWidth={1.5} className="pointer-events-none absolute top-1/2 left-2 -translate-y-1/2 text-ink-3" aria-hidden />
        <TextInput aria-label={t("ml.searchColumns")} placeholder={t("ml.searchColumns")} value={query} onChange={(e) => setQuery(e.target.value)} className="w-full pl-7" />
      </div>
      <ul className="max-h-[420px] divide-y divide-line overflow-y-auto rounded-md border border-line">
        {shown.map((c) => (
          <li key={c.name}>
            <button
              type="button"
              disabled={!c.task}
              onClick={() => onPick(c.name)}
              className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-transparent"
            >
              <span className="min-w-0">
                <span className="font-mono text-xs font-medium text-ink-1">{c.name}</span>
                {c.suggested && c.task && (
                  <span className="ml-2 rounded-full bg-accent-soft px-1.5 py-0.5 text-[10px] text-ink-1">{t("ml.suggested")}</span>
                )}
                {c.reason && <span className="block text-xs text-ink-3">{c.reason}</span>}
              </span>
              {c.task && <span className="shrink-0 text-xs text-ink-2">{taskName(c.task)}</span>}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}

function SettingField({ setting, value, onChange }: { setting: MlSetting; value: unknown; onChange: (value: unknown) => void }) {
  const label = (
    <span className="flex items-center gap-1 text-xs text-ink-2">
      {setting.label}
      {setting.why && <InfoTip label={setting.label} text={setting.why} />}
    </span>
  );
  if (setting.kind === "select") {
    return (
      <label className="flex items-center justify-between gap-3">
        {label}
        <Select aria-label={setting.label} value={String(value)} onChange={(event) => onChange(event.target.value)} className="h-7 text-xs">
          {setting.options.map((option) => (
            <option key={option} value={option}>
              {t(`ml.option.${option}` as MessageKey)}
            </option>
          ))}
        </Select>
      </label>
    );
  }
  return (
    <label className="flex items-center justify-between gap-3">
      {label}
      <TextInput
        aria-label={setting.label}
        type="number"
        value={String(value)}
        min={setting.minimum ?? undefined}
        max={setting.maximum ?? undefined}
        step="any"
        onChange={(event) => onChange(event.target.value === "" ? setting.default : Number(event.target.value))}
        className="h-7 w-24 text-xs"
      />
    </label>
  );
}

function Workbench({
  datasetId,
  candidate,
  candidates,
  rows,
  runId,
  onTarget,
  onRun,
}: {
  datasetId: string;
  candidate: MlCandidate;
  candidates: MlCandidate[];
  rows: number;
  runId: string | undefined;
  onTarget: (name: string) => void;
  onRun: (id: string) => void;
}) {
  const client = useQueryClient();
  const task = candidate.task ?? "regression";
  const runs = useMlRuns(datasetId, candidate.name);
  const shownRunId = runId ?? runs.data?.[0]?.id ?? null;
  const run = useMlRun(datasetId, shownRunId);
  const catalog = useMlCatalog(task, rows, null);
  const model = catalog.data?.[0];
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [jobId, setJobId] = useState<string | null>(null);
  const train = useMlTrain(datasetId);
  const job = useMlJob(jobId);
  const started = useRef(false);
  const [editing, setEditing] = useState(false);
  // Preparation choices: what the user changed, else what the shown run used.
  const [edited, setEdited] = useState<MlChoicesInput | null>(null);
  const choices: MlChoicesInput = edited ?? run.data?.preparation.choices ?? {};

  const settings = useMemo(() => {
    const merged: Record<string, unknown> = {};
    // Shown: what the user changed, else what the last run used (defaults resolved on the data).
    const used = run.data?.model === model?.key ? run.data?.settings : undefined;
    for (const s of model?.settings ?? []) merged[s.key] = values[s.key] ?? used?.[s.key] ?? s.default;
    return merged;
  }, [model, values, run.data]);

  // Only the settings the user changed: the server resolves every other default on the data.
  const changedSettings = Object.keys(values).length ? values : null;
  const launch = () =>
    train.mutate(
      { target: candidate.name, model: model?.key ?? null, settings: changedSettings, choices },
      {
        onSuccess: (created) => {
          setJobId(created.id);
          setEdited(null);
        },
      },
    );
  const pickRun = (id: string) => {
    setEdited(null);
    onRun(id);
  };

  // The reference model trains on its own the first time a target is chosen.
  useEffect(() => {
    if (runs.data && runs.data.length === 0 && !started.current) {
      started.current = true;
      train.mutate({ target: candidate.name, model: null, settings: null }, { onSuccess: (created) => setJobId(created.id) });
    }
  }, [runs.data, candidate.name, train]);

  // When a training ends, show its run and refresh the list.
  const finished = job.data?.status === "done" ? job.data.run_id : null;
  useEffect(() => {
    if (finished) {
      void client.invalidateQueries({ queryKey: ["datasets", datasetId, "ml", "runs", candidate.name] });
      onRun(finished);
    }
  }, [finished, client, datasetId, candidate.name, onRun]);

  const training = train.isPending || job.data?.status === "running";
  const preparation = run.data?.preparation;
  const visible = (s: MlSetting) =>
    !s.shown_when || Object.entries(s.shown_when).every(([key, allowed]) => allowed.includes(String(settings[key])));

  return (
    <div className="grid gap-6 lg:grid-cols-[320px_minmax(0,1fr)]">
      <aside className="space-y-5" aria-label={t("ml.settings")}>
        <section className="space-y-2">
          <label className="flex items-center justify-between gap-3">
            <span className="text-xs text-ink-3">{t("ml.predict")}</span>
            <Select aria-label={t("ml.predict")} value={candidate.name} onChange={(event) => onTarget(event.target.value)} className="h-8 max-w-48 text-[13px]">
              {candidates
                .filter((c) => c.task)
                .map((c) => (
                  <option key={c.name} value={c.name}>
                    {c.name}
                  </option>
                ))}
            </Select>
          </label>
          <p className="text-xs text-ink-2">{t(`ml.taskLong.${task}` as MessageKey)}</p>
          {candidate.reason && <p className="text-xs text-ink-3">{candidate.reason}</p>}
        </section>
        {model && (
          <section className="space-y-2">
            <div>
              <span className="text-xs text-ink-3">{t("ml.model")}</span>
              <p className="font-medium text-ink-1">{model.label}</p>
              <p className="text-xs text-ink-3">{model.description}</p>
            </div>
            {model.settings.filter(visible).map((s) => (
              <SettingField key={s.key} setting={s} value={settings[s.key]} onChange={(value) => setValues({ ...values, [s.key]: value })} />
            ))}
          </section>
        )}
        <section className="space-y-1 text-xs">
          <div className="flex items-center justify-between gap-2">
            <p className="text-ink-3">
              {t("ml.preparation")} · {(edited ? Object.keys(edited).length > 0 : preparation?.custom) ? t("ml.prep.custom") : t("ml.prep.automatic")}
            </p>
            <Button variant="ghost" onClick={() => setEditing(true)} disabled={!model}>
              {t("ml.prep.edit")}
            </Button>
          </div>
          <p className="text-ink-1">{preparation ? preparationSummary(preparation) : t("ml.preparationAuto")}</p>
          {edited && <p className="text-warn">{t("ml.prep.pending")}</p>}
          <p className="pt-1 text-ink-3">{t("ml.validation")}</p>
        </section>
        <PreparationEditor
          open={editing}
          onOpenChange={setEditing}
          datasetId={datasetId}
          target={candidate.name}
          task={task}
          model={model?.key ?? null}
          settings={changedSettings}
          choices={choices}
          onChoices={setEdited}
        />
        <Button variant="primary" onClick={launch} disabled={training || !model}>
          {training ? t(`ml.stage.${job.data?.stage ?? "loading"}` as MessageKey) : t("ml.train")}
        </Button>
        {train.isError && <ErrorNote>{train.error.message}</ErrorNote>}
        {job.data?.status === "failed" && <ErrorNote>{job.data.error}</ErrorNote>}
      </aside>

      <div className={`min-w-0 space-y-5 ${training ? "opacity-60" : ""}`} aria-busy={training}>
        {run.data ? (
          <Results run={run.data} datasetId={datasetId} />
        ) : (
          <div className="flex h-72 items-center justify-center rounded-lg border border-dashed border-line text-ink-3">
            {training ? t("ml.trainingFirst") : t("ml.noRunYet")}
          </div>
        )}
        {runs.data && runs.data.length > 0 && <RunStrip runs={runs.data} shown={run.data} onPick={pickRun} />}
      </div>
    </div>
  );
}

function RunStrip({ runs, shown, onPick }: { runs: NonNullable<ReturnType<typeof useMlRuns>["data"]>; shown: MlRun | undefined; onPick: (id: string) => void }) {
  const best = [...runs].filter((r) => r.score !== null).sort((a, b) => (b.score ?? 0) - (a.score ?? 0))[0];
  return (
    <section aria-label={t("ml.runs")} className="space-y-1.5">
      <h3 className="text-xs text-ink-3">{t("ml.runs")}</h3>
      <div className="flex flex-wrap gap-2">
        {runs.map((r, index) => (
          <button
            key={r.id}
            type="button"
            onClick={() => onPick(r.id)}
            aria-pressed={shown?.id === r.id}
            className={`rounded-md border px-2.5 py-1.5 text-left text-xs ${shown?.id === r.id ? "border-accent bg-accent-soft" : "border-line hover:bg-surface-1"}`}
          >
            <span className="text-ink-1">
              #{runs.length - index} {t(`ml.modelName.${r.model}` as MessageKey)}
              {typeof r.settings.regularization === "string" && r.settings.regularization !== "none"
                ? ` · ${t(`ml.option.${r.settings.regularization}` as MessageKey)}`
                : ""}
              {best?.id === r.id && runs.length > 1 ? " ★" : ""}
            </span>
            <span className="block text-ink-3 tabular-nums">
              {t(`ml.metric.${r.metric}` as MessageKey)} {formatNumber(r.score)} · {r.seconds.toFixed(1)} s
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}

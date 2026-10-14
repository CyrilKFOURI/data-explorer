import { useNavigate, useParams, useSearch } from "@tanstack/react-router";
import { ArrowLeftRight } from "lucide-react";
import { useMemo, useState } from "react";

import type { AnalysisType, Column, Comparison } from "../../api/client";
import { useColumns, useCompare, useDataset } from "../../api/hooks";
import { Plot } from "../../charts/Plot";
import {
  contingencyFigure,
  dateCountsFigure,
  densityFigure,
  groupsFigure,
  scatter3dFigure,
  scatterFigure,
  timelineFigure,
  type GroupView,
  type TableView,
} from "../../features/compare/figures";
import { TestsPanel } from "../../features/compare/TestsPanel";
import { NoRows } from "../../features/filters/NoRows";
import { t } from "../../lib/i18n";
import { Button } from "../../ui/Button";
import { Checkbox, ErrorNote, Field, Select } from "../../ui/fields";
import { SegmentedControl } from "../../ui/SegmentedControl";

export type CompareSearch = { x?: string; y?: string; z?: string; color?: string };

const text = (value: unknown) => (typeof value === "string" && value ? value : undefined);

export function validateCompareSearch(search: Record<string, unknown>): CompareSearch {
  return { x: text(search.x), y: text(search.y), z: text(search.z), color: text(search.color) };
}

type Role = "num" | "cat" | "date";
const ROLE: Partial<Record<AnalysisType, Role>> = {
  numeric_continuous: "num",
  numeric_discrete: "num",
  categorical_nominal: "cat",
  categorical_ordinal: "cat",
  boolean: "cat",
  datetime: "date",
};
const HEIGHT = 460;

export function ComparePage() {
  const { datasetId } = useParams({ from: "/d/$datasetId/compare" });
  const search = useSearch({ from: "/d/$datasetId/compare" });
  const navigate = useNavigate({ from: "/d/$datasetId/compare" });
  const dataset = useDataset(datasetId);
  const columns = useColumns(datasetId, dataset.data?.status === "ready");

  const usable = useMemo(
    () => (columns.data ?? []).filter((c) => !c.excluded && ROLE[c.type]).sort((a, b) => a.position - b.position),
    [columns.data],
  );
  const byName = new Map(usable.map((c) => [c.name, c]));
  const x = search.x && byName.get(search.x);
  const y = search.y && byName.get(search.y);
  const bothNumeric = Boolean(x && y && ROLE[x.type] === "num" && ROLE[y.type] === "num");
  const z = bothNumeric && search.z ? byName.get(search.z) : undefined;
  const color = search.color ? byName.get(search.color) : undefined;
  const colorAllowed = Boolean(x && y && (bothNumeric || ROLE[x.type] === "date" || ROLE[y.type] === "date"));
  const params =
    x && y && x.name !== y.name
      ? { x: x.name, y: y.name, z: z?.name ?? null, color: colorAllowed ? (color?.name ?? null) : null }
      : null;
  const comparison = useCompare(datasetId, params);

  const set = (patch: CompareSearch) =>
    void navigate({ search: (previous) => ({ ...previous, ...patch }), replace: true });

  return (
    <div className="flex flex-col gap-5 px-8 py-6">
      <header className="max-w-prose">
        <h1 className="text-xl font-semibold tracking-tight">{t("compare.title")}</h1>
        <p className="mt-1 text-ink-2">{t("compare.description")}</p>
      </header>

      <div className="flex flex-wrap items-end gap-3">
        <ColumnPicker label="X" value={x ? x.name : ""} columns={usable} onChange={(name) => set({ x: name })} />
        <Button
          variant="ghost"
          icon={ArrowLeftRight}
          iconOnly
          aria-label={t("compare.swap")}
          title={t("compare.swap")}
          disabled={!x || !y}
          onClick={() => set({ x: search.y, y: search.x })}
        />
        <ColumnPicker label="Y" value={y ? y.name : ""} columns={usable} onChange={(name) => set({ y: name })} />
        <ColumnPicker
          label={t("compare.z")}
          value={z?.name ?? ""}
          columns={usable.filter((c) => ROLE[c.type] === "num")}
          optional
          disabled={!bothNumeric}
          hint={bothNumeric ? undefined : t("compare.zHint")}
          onChange={(name) => set({ z: name || undefined })}
        />
        <ColumnPicker
          label={t("compare.color")}
          value={colorAllowed ? (color?.name ?? "") : ""}
          columns={usable.filter((c) => ROLE[c.type] === "cat")}
          optional
          disabled={!colorAllowed}
          hint={colorAllowed ? undefined : t("compare.colorHint")}
          onChange={(name) => set({ color: name || undefined })}
        />
      </div>

      {columns.isPending ? (
        <div className="h-[460px] animate-pulse rounded-lg bg-surface-1" aria-busy="true" />
      ) : !params ? (
        <p className="rounded-lg border border-dashed border-line px-4 py-10 text-center text-ink-2">
          {x && y ? t("compare.differentColumns") : t("compare.pick")}
        </p>
      ) : comparison.isError ? (
        <ErrorNote>{comparison.error.message}</ErrorNote>
      ) : !comparison.data ? (
        <div className="h-[460px] animate-pulse rounded-lg bg-surface-1" aria-busy="true" />
      ) : comparison.data.total === 0 ? (
        <NoRows datasetId={datasetId} />
      ) : (
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
          {comparison.data.rows < 3 ? (
            <p className="rounded-lg border border-line bg-surface-1 px-4 py-10 text-center text-ink-2">
              {comparison.data.message}
            </p>
          ) : (
            <ChartArea key={`${params.x}|${params.y}|${params.z}`} result={comparison.data} />
          )}
          <TestsPanel result={comparison.data} />
        </div>
      )}
    </div>
  );
}

function ColumnPicker({
  label,
  value,
  columns,
  onChange,
  optional = false,
  disabled = false,
  hint,
}: {
  label: string;
  value: string;
  columns: Column[];
  onChange: (name: string) => void;
  optional?: boolean;
  disabled?: boolean;
  hint?: string;
}) {
  return (
    <Field label={label}>
      <Select value={value} onChange={(event) => onChange(event.target.value)} disabled={disabled} title={hint} className="w-48">
        <option value="">{optional ? t("compare.none") : t("compare.choose")}</option>
        {columns.map((column) => (
          <option key={column.name} value={column.name}>
            {column.name}
          </option>
        ))}
      </Select>
    </Field>
  );
}

type View = "points" | "density" | "3d" | GroupView | TableView | "series";

function viewsFor(result: Comparison): View[] {
  if (result.kind === "scatter") return result.z ? ["3d", "points", "density"] : ["points", "density"];
  if (result.kind === "groups") return ["box", "violin", "means"];
  if (result.kind === "contingency") return ["heatmap", "stacked"];
  return ["series"];
}

function pickView(result: Comparison, chosen: View | null): View {
  const views = viewsFor(result);
  return chosen && views.includes(chosen) ? chosen : (views[0] ?? "series");
}

function figureFor(result: Comparison, view: View, regression: boolean) {
  if (view === "3d") return scatter3dFigure(result);
  if (view === "points") return scatterFigure(result, regression);
  if (view === "density") return densityFigure(result);
  if (view === "box" || view === "violin" || view === "means") return groupsFigure(result, view);
  if (view === "heatmap" || view === "stacked") return contingencyFigure(result, view);
  return result.kind === "date_counts" ? dateCountsFigure(result) : timelineFigure(result);
}

function ChartArea({ result }: { result: Comparison }) {
  const [chosen, setChosen] = useState<View | null>(null);
  const [regression, setRegression] = useState(true);
  const view = pickView(result, chosen);
  const figure = useMemo(() => figureFor(result, view, regression), [result, view, regression]);
  const views = viewsFor(result);

  return (
    <section className="min-w-0 rounded-lg border border-line bg-surface-1 p-3">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        {views.length > 1 ? (
          <SegmentedControl
            label={t("compare.view")}
            value={view}
            options={views.map((value) => ({ value, label: t(`compare.view.${value}`) }))}
            onChange={setChosen}
          />
        ) : (
          <span className="text-xs text-ink-3">{result.step ? t("compare.step", { step: result.step }) : ""}</span>
        )}
        {view === "points" && result.regression && (
          <Checkbox
            label={t("compare.regression", { r2: result.regression.r2 === null ? "—" : result.regression.r2.toFixed(3) })}
            checked={regression}
            onChange={(event) => setRegression(event.target.checked)}
            className="text-xs text-ink-2"
          />
        )}
      </div>
      <Plot figure={figure} height={HEIGHT} label={t("compare.chartLabel", { x: result.x, y: result.y })} />
      {view === "density" && <p className="mt-1.5 text-xs text-ink-3">{t("compare.densityNote")}</p>}
      {(view === "points" || view === "3d") && result.sample && (
        <p className="mt-1.5 text-xs text-ink-3">{t("compare.sampleNote", { sample: result.sample.toLocaleString("en-US"), rows: result.rows.toLocaleString("en-US") })}</p>
      )}
    </section>
  );
}

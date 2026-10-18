import {
  keepPreviousData,
  useMutation,
  useQueries,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { useActiveFilters, type Condition } from "./filters";
import {
  api,
  type ChartParams,
  type CompareParams,
  type SeriesParams,
  type SeriesSectionKey,
  type CorrelationMethod,
  type ColumnChange,
  type Dataset,
  type ImportOptions,
  type MlChoicesInput,
  type MlClasses,
  type OutlierMethod,
  type DetectionSettings,
  type RowsView,
  type SourceOptions,
} from "./client";

export const queryKeys = {
  health: ["health"] as const,
  datasets: ["datasets"] as const,
  dataset: (id: string) => ["datasets", id] as const,
  schema: (id: string) => ["datasets", id, "schema"] as const,
  head: (id: string) => ["datasets", id, "head"] as const,
  job: (id: string) => ["jobs", id] as const,
  preview: (path: string, options: SourceOptions) =>
    ["preview", path, options] as const,
  browse: (path: string | null) => ["browse", path] as const,
  samples: ["samples"] as const,
  columns: (id: string) => ["datasets", id, "columns"] as const,
  roles: ["column-roles"] as const,
  overview: (id: string, filters: Condition[] = []) =>
    ["datasets", id, "overview", filters] as const,
  chart: (
    id: string,
    column: string,
    params: ChartParams,
    filters: Condition[] = [],
  ) => ["datasets", id, "chart", column, params, filters] as const,
  summaries: (id: string, filters: Condition[]) =>
    ["datasets", id, "summaries", filters] as const,
  variable: (id: string, column: string, filters: Condition[] = []) =>
    ["datasets", id, "variable", column, filters] as const,
  fit: (id: string, column: string, filters: Condition[] = []) =>
    ["datasets", id, "variable", column, "fit", filters] as const,
  outliers: (
    id: string,
    column: string,
    method: OutlierMethod,
    filters: Condition[] = [],
  ) =>
    ["datasets", id, "variable", column, "outliers", method, filters] as const,
  savedFilters: (id: string) => ["datasets", id, "saved-filters"] as const,
  correlations: (
    id: string,
    method: CorrelationMethod,
    columns: string[] | null,
    filters: Condition[],
  ) => ["datasets", id, "correlations", method, columns, filters] as const,
  compare: (id: string, params: CompareParams, filters: Condition[]) =>
    ["datasets", id, "compare", params, filters] as const,
  series: (
    id: string,
    section: string,
    params: SeriesParams,
    extra: Record<string, string>,
    filters: Condition[],
  ) => ["datasets", id, "timeseries", section, params, extra, filters] as const,
  settings: ["settings"] as const,
  storage: ["storage"] as const,
  rows: (id: string, view: RowsView, filters: Condition[], block: number) =>
    ["datasets", id, "rows", view, filters, block] as const,
};

const isImporting = (datasets: Dataset[] | undefined) =>
  datasets?.some((dataset) => dataset.status === "importing") ?? false;

export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: api.health,
    refetchInterval: 15_000,
    retry: false,
  });
}

export function useDatasets() {
  return useQuery({
    queryKey: queryKeys.datasets,
    queryFn: api.datasets,
    refetchInterval: (query) => (isImporting(query.state.data) ? 1_000 : false),
    refetchIntervalInBackground: true,
  });
}

export function useDataset(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.dataset(id ?? ""),
    queryFn: () => api.dataset(id ?? ""),
    enabled: Boolean(id),
    refetchInterval: (query) =>
      query.state.data?.status === "importing" ? 1_000 : false,
  });
}

export function useSchema(id: string, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.schema(id),
    queryFn: () => api.schema(id),
    enabled,
  });
}

export function useHead(id: string, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.head(id),
    queryFn: () => api.head(id),
    enabled,
  });
}

export function useJob(id: string | null) {
  return useQuery({
    queryKey: queryKeys.job(id ?? ""),
    queryFn: () => api.job(id ?? ""),
    enabled: Boolean(id),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "done" || status === "failed" ? false : 500;
    },
    // Keep following an import when the user switches to another tab.
    refetchIntervalInBackground: true,
  });
}

export function usePreview(path: string | null, options: SourceOptions) {
  return useQuery({
    queryKey: queryKeys.preview(path ?? "", options),
    queryFn: () => api.preview(path ?? "", options),
    enabled: Boolean(path),
    retry: false,
    staleTime: Infinity,
    placeholderData: (previous) => previous,
  });
}

export function useBrowse(path: string | null, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.browse(path),
    queryFn: () => api.browse(path),
    enabled,
    retry: false,
  });
}

export function useSamples() {
  return useQuery({
    queryKey: queryKeys.samples,
    queryFn: api.samples,
    staleTime: Infinity,
  });
}

export function useUpload() {
  return useMutation({ mutationFn: api.upload });
}

export function useImportDataset() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      path: string;
      name: string | null;
      options: ImportOptions;
    }) => api.importDataset(input.path, input.name, input.options),
    onSettled: () => client.invalidateQueries({ queryKey: queryKeys.datasets }),
  });
}

export function useRenameDataset() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: { id: string; name: string }) =>
      api.renameDataset(input.id, input.name),
    onSuccess: () => client.invalidateQueries({ queryKey: queryKeys.datasets }),
  });
}

export function useDeleteDataset() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: api.deleteDataset,
    onSuccess: () => client.invalidateQueries({ queryKey: queryKeys.datasets }),
  });
}

export function useReimportDataset() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: api.reimportDataset,
    onSuccess: () => client.invalidateQueries({ queryKey: queryKeys.datasets }),
  });
}

export function useOpenDataset() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: api.openDataset,
    onSuccess: (dataset) => {
      client.setQueryData(queryKeys.dataset(dataset.id), dataset);
      void client.invalidateQueries({
        queryKey: queryKeys.datasets,
        exact: true,
      });
    },
  });
}

export function useColumns(id: string, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.columns(id),
    queryFn: () => api.columns(id),
    enabled,
  });
}

export function useRoles() {
  return useQuery({
    queryKey: queryKeys.roles,
    queryFn: api.roles,
    staleTime: Infinity,
  });
}

/** Column corrections; the server answers with all columns, written straight to the cache. */
export function useUpdateColumns(id: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (changes: ColumnChange[]) => api.updateColumns(id, changes),
    onSuccess: (columns) => {
      client.setQueryData(queryKeys.columns(id), columns);
      void client.invalidateQueries({
        queryKey: queryKeys.dataset(id),
        exact: true,
      });
      void client.invalidateQueries({ queryKey: queryKeys.overview(id) });
      void client.invalidateQueries({ queryKey: ["datasets", id, "chart"] });
      void client.invalidateQueries({ queryKey: ["datasets", id, "variable"] });
    },
  });
}

export function useDetectColumns(id: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () => api.detectColumns(id),
    onSuccess: (columns) => client.setQueryData(queryKeys.columns(id), columns),
  });
}

export function useReviewTypes(id: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () => api.reviewTypes(id),
    onSuccess: (dataset) => {
      client.setQueryData(queryKeys.dataset(id), dataset);
      void client.invalidateQueries({
        queryKey: queryKeys.datasets,
        exact: true,
      });
    },
  });
}

/** Overview of the rows that pass the active filters. */
export function useOverview(id: string, enabled: boolean) {
  const filters = useActiveFilters(id);
  return useQuery({
    queryKey: queryKeys.overview(id, filters),
    queryFn: () => api.overview(id, filters),
    enabled,
    placeholderData: (previous) => previous,
  });
}

/** Chart data over the filtered rows; `unfiltered` reads every row (e.g. values to pick from). */
export function useChart(
  id: string,
  column: string,
  params: ChartParams,
  enabled: boolean,
  options: { unfiltered?: boolean } = {},
) {
  const active = useActiveFilters(id);
  const filters = options.unfiltered ? [] : active;
  return useQuery({
    queryKey: queryKeys.chart(id, column, params, filters),
    queryFn: () => api.chart(id, column, params, filters),
    enabled,
    staleTime: 60_000,
    placeholderData: (previous) => previous,
  });
}

export function useVariable(id: string, column: string, enabled = true) {
  const filters = useActiveFilters(id);
  return useQuery({
    queryKey: queryKeys.variable(id, column, filters),
    queryFn: () => api.variable(id, column, filters),
    enabled,
    staleTime: 60_000,
  });
}

export function useFit(id: string, column: string, enabled: boolean) {
  const filters = useActiveFilters(id);
  return useQuery({
    queryKey: queryKeys.fit(id, column, filters),
    queryFn: () => api.fit(id, column, filters),
    enabled,
    staleTime: 60_000,
  });
}

export function useOutliers(
  id: string,
  column: string,
  method: OutlierMethod,
  enabled: boolean,
) {
  const filters = useActiveFilters(id);
  return useQuery({
    queryKey: queryKeys.outliers(id, column, method, filters),
    queryFn: () => api.outliers(id, column, method, filters),
    enabled,
    staleTime: 60_000,
    placeholderData: (previous) => previous,
  });
}

/** Column summaries over the filtered rows (only fetched while filters are active). */
export function useColumnSummaries(id: string, enabled: boolean) {
  const filters = useActiveFilters(id);
  return useQuery({
    queryKey: queryKeys.summaries(id, filters),
    queryFn: () => api.summaries(id, filters),
    enabled: enabled && filters.length > 0,
    placeholderData: (previous) => previous,
  });
}

export function useSavedFilters(id: string) {
  return useQuery({
    queryKey: queryKeys.savedFilters(id),
    queryFn: () => api.savedFilters(id),
  });
}

export function useSaveFilter(id: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: { name: string; conditions: Condition[] }) =>
      api.saveFilter(id, input.name, input.conditions),
    onSuccess: () =>
      client.invalidateQueries({ queryKey: queryKeys.savedFilters(id) }),
  });
}

export function useDeleteSavedFilter(id: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (filterId: string) => api.deleteSavedFilter(id, filterId),
    onSuccess: () =>
      client.invalidateQueries({ queryKey: queryKeys.savedFilters(id) }),
  });
}

/** Two or three columns compared over the filtered rows. */
export function useCompare(id: string, params: CompareParams | null) {
  const filters = useActiveFilters(id);
  return useQuery({
    queryKey: queryKeys.compare(id, params ?? { x: "", y: "" }, filters),
    queryFn: () => api.compare(id, params as CompareParams, filters),
    enabled: Boolean(params),
    staleTime: 60_000,
    placeholderData: (previous) => previous,
    retry: false,
  });
}

/** One section of the Time series page; `enabled` lets a section wait until it is on screen. */
export function useSeriesSection<T>(
  id: string,
  section: SeriesSectionKey,
  params: SeriesParams,
  extra: Record<string, string>,
  enabled = true,
) {
  const filters = useActiveFilters(id);
  return useQuery({
    queryKey: queryKeys.series(id, section, params, extra, filters),
    queryFn: () => api.seriesSection<T>(id, section, params, extra, filters),
    enabled,
    staleTime: 60_000,
    placeholderData: (previous) => previous,
    retry: false,
  });
}

/** Start (or reuse) a forecast job for the current series and filters. */
export function useStartForecast(id: string) {
  const filters = useActiveFilters(id);
  return useMutation({
    mutationFn: ({
      params,
      extra,
    }: {
      params: SeriesParams;
      extra: Record<string, string>;
    }) => api.startForecast(id, params, extra, filters),
  });
}

/** Follow a forecast job until it ends (also while the tab is in the background). */
export function useForecastJob(jobId: string | null) {
  return useQuery({
    queryKey: ["forecast-jobs", jobId ?? ""],
    queryFn: () => api.forecastJob(jobId ?? ""),
    enabled: Boolean(jobId),
    refetchInterval: (query) =>
      query.state.data?.status === "running" || !query.state.data ? 500 : false,
    refetchIntervalInBackground: true,
    retry: false,
  });
}

export function useCancelForecast() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => api.cancelForecast(jobId),
    onSuccess: (job) => client.setQueryData(["forecast-jobs", job.id], job),
  });
}

/** Every column as a possible target, through the active filters. */
export function useMlTargets(id: string, enabled: boolean) {
  const filters = useActiveFilters(id);
  return useQuery({
    queryKey: ["datasets", id, "ml", "targets", filters],
    queryFn: () => api.mlTargets(id, filters),
    enabled,
    staleTime: 60_000,
  });
}

export function useMlCatalog(task: string | null, rows: number, minority: number | null) {
  return useQuery({
    queryKey: ["ml", "catalog", task, rows, minority],
    queryFn: () => api.mlCatalog(task ?? "regression", rows, minority),
    enabled: Boolean(task),
    staleTime: Infinity,
  });
}

export function useMlTrain(id: string) {
  const filters = useActiveFilters(id);
  return useMutation({
    mutationFn: ({
      target,
      model,
      settings,
      choices,
      classes,
    }: {
      target: string;
      model: string | null;
      settings: Record<string, unknown> | null;
      choices?: MlChoicesInput | null;
      classes?: MlClasses | null;
    }) => api.mlTrain(id, target, model, settings, filters, choices, classes),
  });
}

/** The preparation the next training would use, with its first prepared rows. */
export function useMlPreparation(
  id: string,
  target: string,
  model: string | null,
  settings: Record<string, unknown> | null,
  choices: MlChoicesInput,
  enabled: boolean,
  classes: MlClasses | null = null,
) {
  const filters = useActiveFilters(id);
  return useQuery({
    queryKey: ["datasets", id, "ml", "preparation", target, model, settings, choices, classes, filters],
    queryFn: () => api.mlPreparation(id, target, model, settings, choices, filters, classes),
    enabled,
    placeholderData: keepPreviousData,
    staleTime: 60_000,
    retry: false,
  });
}

/** A numeric target's distribution, to cut it into classes in the browser. */
export function useMlDistribution(id: string, column: string, enabled: boolean) {
  const filters = useActiveFilters(id);
  return useQuery({
    queryKey: ["datasets", id, "ml", "distribution", column, filters],
    queryFn: () => api.mlDistribution(id, column, filters),
    enabled,
    staleTime: 60_000,
  });
}

/** Follow a training until it ends (also while the tab is in the background). */
export function useMlJob(jobId: string | null) {
  return useQuery({
    queryKey: ["ml", "jobs", jobId ?? ""],
    queryFn: () => api.mlJob(jobId ?? ""),
    enabled: Boolean(jobId),
    refetchInterval: (query) => (query.state.data?.status === "running" || !query.state.data ? 400 : false),
    refetchIntervalInBackground: true,
    retry: false,
  });
}

export function useMlRuns(id: string, target: string | null) {
  return useQuery({
    queryKey: ["datasets", id, "ml", "runs", target ?? ""],
    queryFn: () => api.mlRuns(id, target ?? ""),
    enabled: Boolean(target),
  });
}

export function useMlRun(id: string, runId: string | null) {
  return useQuery({
    queryKey: ["datasets", id, "ml", "run", runId ?? ""],
    queryFn: () => api.mlRun(id, runId ?? ""),
    enabled: Boolean(runId),
    staleTime: Infinity,
  });
}

/** Association matrix and insights over the filtered rows. */
export function useCorrelations(
  id: string,
  method: CorrelationMethod,
  columns: string[] | null,
  enabled: boolean,
) {
  const filters = useActiveFilters(id);
  return useQuery({
    queryKey: queryKeys.correlations(id, method, columns, filters),
    queryFn: () => api.correlations(id, method, columns, filters),
    enabled,
    staleTime: 60_000,
    placeholderData: (previous) => previous,
  });
}

export const ROW_BLOCK = 100;

/** Blocks of rows of the Data page (block k = rows k*100 … k*100+99 of the view). */
export function useRowBlocks(
  id: string,
  view: RowsView,
  blocks: number[],
  enabled: boolean,
) {
  const filters = useActiveFilters(id);
  return useQueries({
    queries: blocks.map((block) => ({
      queryKey: queryKeys.rows(id, view, filters, block),
      queryFn: () => api.rows(id, view, block * ROW_BLOCK, ROW_BLOCK, filters),
      enabled,
      staleTime: 60_000,
      placeholderData: block === 0 ? keepPreviousData : undefined,
    })),
  });
}

export function useSettings() {
  return useQuery({ queryKey: queryKeys.settings, queryFn: api.settings });
}

export function useUpdateSettings() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (detection: DetectionSettings) => api.updateSettings(detection),
    onSuccess: (saved) => client.setQueryData(queryKeys.settings, saved),
  });
}

export function useStorage() {
  return useQuery({ queryKey: queryKeys.storage, queryFn: api.storage });
}

/** Empties the server's in-memory caches and this page's cached results. */
export function useClearCaches() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: api.clearCaches,
    onSuccess: () => client.invalidateQueries({ queryKey: ["datasets"] }),
  });
}

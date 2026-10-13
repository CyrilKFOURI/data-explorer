import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  api,
  type ChartParams,
  type ColumnChange,
  type Dataset,
  type ImportOptions,
  type SourceOptions,
} from "./client";

export const queryKeys = {
  health: ["health"] as const,
  datasets: ["datasets"] as const,
  dataset: (id: string) => ["datasets", id] as const,
  schema: (id: string) => ["datasets", id, "schema"] as const,
  head: (id: string) => ["datasets", id, "head"] as const,
  job: (id: string) => ["jobs", id] as const,
  preview: (path: string, options: SourceOptions) => ["preview", path, options] as const,
  browse: (path: string | null) => ["browse", path] as const,
  samples: ["samples"] as const,
  columns: (id: string) => ["datasets", id, "columns"] as const,
  roles: ["column-roles"] as const,
  overview: (id: string) => ["datasets", id, "overview"] as const,
  chart: (id: string, column: string, params: ChartParams) =>
    ["datasets", id, "chart", column, params] as const,
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
    refetchInterval: (query) => (query.state.data?.status === "importing" ? 1_000 : false),
  });
}

export function useSchema(id: string, enabled: boolean) {
  return useQuery({ queryKey: queryKeys.schema(id), queryFn: () => api.schema(id), enabled });
}

export function useHead(id: string, enabled: boolean) {
  return useQuery({ queryKey: queryKeys.head(id), queryFn: () => api.head(id), enabled });
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
  return useQuery({ queryKey: queryKeys.samples, queryFn: api.samples, staleTime: Infinity });
}

export function useUpload() {
  return useMutation({ mutationFn: api.upload });
}

export function useImportDataset() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: { path: string; name: string | null; options: ImportOptions }) =>
      api.importDataset(input.path, input.name, input.options),
    onSettled: () => client.invalidateQueries({ queryKey: queryKeys.datasets }),
  });
}

export function useRenameDataset() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: { id: string; name: string }) => api.renameDataset(input.id, input.name),
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
      void client.invalidateQueries({ queryKey: queryKeys.datasets, exact: true });
    },
  });
}

export function useColumns(id: string, enabled: boolean) {
  return useQuery({ queryKey: queryKeys.columns(id), queryFn: () => api.columns(id), enabled });
}

export function useRoles() {
  return useQuery({ queryKey: queryKeys.roles, queryFn: api.roles, staleTime: Infinity });
}

/** Column corrections; the server answers with all columns, written straight to the cache. */
export function useUpdateColumns(id: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (changes: ColumnChange[]) => api.updateColumns(id, changes),
    onSuccess: (columns) => {
      client.setQueryData(queryKeys.columns(id), columns);
      void client.invalidateQueries({ queryKey: queryKeys.dataset(id), exact: true });
      void client.invalidateQueries({ queryKey: queryKeys.overview(id) });
      void client.invalidateQueries({ queryKey: ["datasets", id, "chart"] });
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
      void client.invalidateQueries({ queryKey: queryKeys.datasets, exact: true });
    },
  });
}

export function useOverview(id: string, enabled: boolean) {
  return useQuery({ queryKey: queryKeys.overview(id), queryFn: () => api.overview(id), enabled });
}

export function useChart(id: string, column: string, params: ChartParams, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.chart(id, column, params),
    queryFn: () => api.chart(id, column, params),
    enabled,
    staleTime: 60_000,
    placeholderData: (previous) => previous,
  });
}

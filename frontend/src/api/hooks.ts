import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type Dataset, type ImportOptions, type SourceOptions } from "./client";

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

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import { api, reportFileUrl } from "../../api/client";
import { useActiveFilters } from "../../api/filters";

const downloaded = new Set<string>();

/** The dataset's HTML report (025): start it over the active filters, follow it, download it once
 * done. The job id lives in the query cache, so the Overview and Data pages share it. */
export function useReport(datasetId: string) {
  const client = useQueryClient();
  const filters = useActiveFilters(datasetId);
  const key = ["report", datasetId];
  const { data: jobId } = useQuery<string | null>({
    queryKey: key,
    queryFn: () => null,
    initialData: null,
    staleTime: Infinity,
  });
  const job = useQuery({
    queryKey: ["report-jobs", jobId],
    queryFn: () => api.reportJob(jobId ?? ""),
    enabled: Boolean(jobId),
    refetchInterval: (query) =>
      query.state.data?.status === "running" || !query.state.data ? 400 : false,
    refetchIntervalInBackground: true,
    retry: false,
  });
  const start = useMutation({
    mutationFn: () => api.reportStart(datasetId, filters),
    onSuccess: (started) => {
      client.setQueryData(["report-jobs", started.id], started);
      client.setQueryData(key, started.id);
    },
  });
  const cancel = useMutation({
    mutationFn: (id: string) => api.reportCancel(id),
    onSuccess: (cancelled) =>
      client.setQueryData(["report-jobs", cancelled.id], cancelled),
  });

  const current = jobId ? job.data : undefined;
  useEffect(() => {
    if (current?.status !== "done" || downloaded.has(current.id)) return;
    downloaded.add(current.id);
    const link = document.createElement("a");
    link.href = reportFileUrl(current.id);
    link.download = current.file_name ?? "report.html";
    document.body.append(link);
    link.click();
    link.remove();
  }, [current]);

  return {
    job: current,
    running: start.isPending || current?.status === "running",
    error:
      start.error?.message ??
      (current?.status === "failed" ? current.error : null),
    start: () => start.mutate(),
    cancel: () => {
      if (current) cancel.mutate(current.id);
    },
  };
}

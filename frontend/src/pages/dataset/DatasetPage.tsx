import { useParams } from "@tanstack/react-router";
import { useEffect } from "react";

import { useDataset, useHead, useOpenDataset, useSchema } from "../../api/hooks";
import { StatusBadge } from "../../features/datasets/StatusBadge";
import { PreviewTable } from "../../features/import/PreviewTable";
import { formatBytes, formatCount } from "../../lib/format";
import { t } from "../../lib/i18n";
import { ErrorNote } from "../../ui/fields";

/** Provisional dataset summary until the Columns and Overview pages exist (features 002–003). */
export function DatasetPage() {
  const { datasetId } = useParams({ from: "/d/$datasetId" });
  const dataset = useDataset(datasetId);
  const ready = dataset.data?.status === "ready";
  const schema = useSchema(datasetId, ready);
  const head = useHead(datasetId, ready);
  const markOpened = useOpenDataset();

  useEffect(() => {
    markOpened.mutate(datasetId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasetId]);

  if (dataset.isPending) return <p className="px-8 py-8 text-ink-3">{t("dataset.loading")}</p>;
  if (dataset.isError)
    return (
      <div className="px-8 py-8">
        <ErrorNote>{dataset.error.message}</ErrorNote>
      </div>
    );

  const data = dataset.data;
  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 px-8 py-8">
      <header>
        <div className="flex items-center gap-3">
          <h1 className="truncate text-xl font-semibold tracking-tight">{data.name}</h1>
          <StatusBadge dataset={data} />
        </div>
        <p className="mt-1 text-ink-2 tabular-nums">
          {t("dataset.meta", {
            rows: formatCount(data.row_count),
            columns: formatCount(data.col_count),
            size: formatBytes(data.size_bytes),
          })}
          {data.sample_pct < 100 && ` · ${t("dataset.sampled", { pct: String(data.sample_pct) })}`}
        </p>
        <p className="mt-0.5 truncate font-mono text-[11px] text-ink-3" title={data.source_path}>
          {data.source_path}
        </p>
      </header>

      {data.status === "importing" && <p className="text-ink-2">{t("dataset.importing")}</p>}
      {data.status === "error" && <ErrorNote>{data.error ?? t("dataset.failed")}</ErrorNote>}

      {ready && (
        <>
          <section>
            <h2 className="mb-2 text-xs text-ink-3">{t("dataset.firstRows")}</h2>
            {head.data && schema.data && (
              <PreviewTable columns={schema.data} rows={head.data.rows} />
            )}
          </section>

          <section>
            <h2 className="mb-2 text-xs text-ink-3">
              {t("dataset.columns")} · {schema.data?.length ?? "…"}
            </h2>
            <ul className="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-px overflow-hidden rounded-lg border border-line bg-line">
              {schema.data?.map((column) => (
                <li key={column.name} className="flex items-baseline justify-between gap-3 bg-surface-1 px-3 py-2">
                  <span className="truncate font-mono text-xs">{column.name}</span>
                  <span className="shrink-0 text-[11px] text-ink-3 lowercase">{column.dtype}</span>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-xs text-ink-3">{t("dataset.next")}</p>
          </section>
        </>
      )}
    </div>
  );
}

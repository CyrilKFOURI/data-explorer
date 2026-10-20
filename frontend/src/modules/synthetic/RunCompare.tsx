import { X } from "lucide-react";

import { useSyntheticCompare } from "../../api/hooks";
import { Plot } from "../../charts/Plot";
import { t, type MessageKey } from "../../lib/i18n";
import { Button } from "../../ui/Button";
import { COMPARED, compareFigure } from "./figures";
import { pct } from "./format";
import { Table } from "./Report";

/** 2 to 5 runs side by side: every score, the best of each row marked, grouped bars. */
export function RunCompare({ datasetId, runIds, onClose }: { datasetId: string; runIds: string[]; onClose: () => void }) {
  const compare = useSyntheticCompare(datasetId, runIds);
  const runs = compare.data ?? [];
  const labels = Object.fromEntries(COMPARED.map((key) => [key, t(`synthetic.${key}` as MessageKey)]));
  return (
    <section className="space-y-3 border-y border-line py-4" aria-label={t("synthetic.compareRuns")}>
      <div className="flex items-center justify-between">
        <h2 className="text-[15px] font-semibold text-ink-1">{t("synthetic.compareRuns")}</h2>
        <Button icon={X} variant="ghost" onClick={onClose}>
          {t("synthetic.close")}
        </Button>
      </div>
      {runs.length > 0 && (
        <div className="grid gap-6 xl:grid-cols-2">
          <Table caption={t("synthetic.scores")} head={["", ...runs.map((r) => `${r.method_label} · ${r.id.slice(0, 4)}`)]}>
            {COMPARED.map((key) => {
              const values = runs.map((r) => r.scores[key] ?? null);
              const best = Math.max(...values.map((v) => v ?? -1));
              return (
                <tr key={key} className="border-b border-line/60">
                  <td className="py-1.5 pr-3 text-ink-2">{labels[key]}</td>
                  {values.map((v, i) => (
                    <td key={i} className={`py-1.5 pr-3 text-right ${v !== null && v === best && values.filter((x) => x === best).length < runs.length ? "font-semibold text-ink-1" : ""}`}>
                      {pct(v)}
                    </td>
                  ))}
                </tr>
              );
            })}
            <tr className="border-b border-line/60">
              <td className="py-1.5 pr-3 text-ink-2">{t("synthetic.device")}</td>
              {runs.map((r) => (
                <td key={r.id} className="py-1.5 pr-3 text-right text-xs">
                  {r.device ?? "–"}
                </td>
              ))}
            </tr>
            <tr className="border-b border-line/60">
              <td className="py-1.5 pr-3 text-ink-2">{t("synthetic.duration")}</td>
              {runs.map((r) => (
                <td key={r.id} className="py-1.5 pr-3 text-right">
                  {r.seconds.toFixed(1)} s
                </td>
              ))}
            </tr>
          </Table>
          <Plot figure={compareFigure(runs, labels)} height={260} label={t("synthetic.compareRuns")} />
        </div>
      )}
    </section>
  );
}

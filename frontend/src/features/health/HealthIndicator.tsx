import { useHealth } from "../../api/hooks";
import { t } from "../../lib/i18n";

export function HealthIndicator() {
  const { data, isPending, isError } = useHealth();

  let dot = "bg-ink-3";
  let message = t("health.checking");
  if (isError) {
    dot = "bg-bad";
    message = t("health.down");
  } else if (data?.status === "ok") {
    dot = "bg-ok";
    message = t("health.ok", { version: data.version });
  } else if (data) {
    dot = "bg-warn";
    message = t("health.degraded");
  }

  return (
    <p role="status" aria-busy={isPending} className="flex items-center gap-2 text-xs text-ink-2">
      <span aria-hidden className={`size-1.5 rounded-full ${dot}`} />
      {message}
    </p>
  );
}

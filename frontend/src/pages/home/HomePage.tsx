import { HealthIndicator } from "../../features/health/HealthIndicator";
import { t } from "../../lib/i18n";
import { PageHeader } from "../../ui/PageHeader";

export function HomePage() {
  return (
    <div className="flex min-h-full flex-col px-8 py-10">
      <PageHeader title={t("home.title")} description={t("home.body")} />
      <div className="mt-auto pt-10">
        <HealthIndicator />
      </div>
    </div>
  );
}

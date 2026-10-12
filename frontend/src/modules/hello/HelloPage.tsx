import { t } from "../../lib/i18n";
import { PageHeader } from "../../ui/PageHeader";

export function HelloPage() {
  return (
    <div className="px-8 py-8">
      <PageHeader title={t("module.hello.title")} description={t("module.hello.body")} />
    </div>
  );
}

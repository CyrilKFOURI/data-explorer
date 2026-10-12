import type { ReactNode } from "react";

import { ThemeSwitcher } from "../../features/theme/ThemeSwitcher";
import { t } from "../../lib/i18n";
import { densityPreference, usePreference } from "../../lib/preferences";
import { PageHeader } from "../../ui/PageHeader";
import { SegmentedControl } from "../../ui/SegmentedControl";

export function SettingsPage() {
  const [density, setDensity] = usePreference(densityPreference);

  return (
    <div className="px-8 py-8">
      <PageHeader title={t("settings.title")} />

      <section className="mt-8 max-w-2xl">
        <h2 className="border-b border-line pb-2 text-sm font-medium">
          {t("settings.appearance")}
        </h2>
        <dl className="divide-y divide-line">
          <SettingRow label={t("theme.label")} hint={t("settings.themeHint")}>
            <ThemeSwitcher />
          </SettingRow>
          <SettingRow label={t("density.label")} hint={t("settings.densityHint")}>
            <SegmentedControl
              label={t("density.label")}
              value={density}
              onChange={setDensity}
              options={[
                { value: "compact", label: t("density.compact") },
                { value: "comfortable", label: t("density.comfortable") },
              ]}
            />
          </SettingRow>
        </dl>
      </section>
    </div>
  );
}

function SettingRow({ label, hint, children }: { label: string; hint: string; children: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-6 py-3">
      <div>
        <dt className="text-ink-1">{label}</dt>
        <dd className="text-xs text-ink-3">{hint}</dd>
      </div>
      {children}
    </div>
  );
}

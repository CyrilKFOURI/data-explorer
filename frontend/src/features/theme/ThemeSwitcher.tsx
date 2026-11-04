import { Monitor, Moon, Sun } from "lucide-react";

import { t } from "../../lib/i18n";
import { themePreference, usePreference } from "../../lib/preferences";
import { SegmentedControl } from "../../ui/SegmentedControl";

export function ThemeSwitcher({ iconOnly = false }: { iconOnly?: boolean }) {
  const [theme, setTheme] = usePreference(themePreference);
  return (
    <SegmentedControl
      label={t("theme.label")}
      value={theme}
      onChange={setTheme}
      iconOnly={iconOnly}
      options={[
        { value: "system", label: t("theme.system"), icon: Monitor },
        { value: "light", label: t("theme.light"), icon: Sun },
        { value: "dark", label: t("theme.dark"), icon: Moon },
      ]}
    />
  );
}

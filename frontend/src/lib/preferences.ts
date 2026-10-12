import { useState } from "react";

/**
 * A UI preference stored in localStorage and mirrored as a `data-*` attribute on <html>,
 * so CSS tokens can react to it. The default value removes the attribute.
 */
export type Preference<T extends string> = {
  storageKey: string;
  attribute: string;
  values: readonly T[];
  defaultValue: T;
};

export const themePreference: Preference<"system" | "light" | "dark"> = {
  storageKey: "de.theme",
  attribute: "theme",
  values: ["system", "light", "dark"],
  defaultValue: "system",
};

export const densityPreference: Preference<"compact" | "comfortable"> = {
  storageKey: "de.density",
  attribute: "density",
  values: ["compact", "comfortable"],
  defaultValue: "compact",
};

export function readPreference<T extends string>(preference: Preference<T>): T {
  try {
    const stored = localStorage.getItem(preference.storageKey);
    return preference.values.find((value) => value === stored) ?? preference.defaultValue;
  } catch {
    return preference.defaultValue;
  }
}

export function applyPreference<T extends string>(
  preference: Preference<T>,
  value: T,
  root: HTMLElement = document.documentElement,
): void {
  if (value === preference.defaultValue) delete root.dataset[preference.attribute];
  else root.dataset[preference.attribute] = value;
}

export function savePreference<T extends string>(preference: Preference<T>, value: T): void {
  try {
    localStorage.setItem(preference.storageKey, value);
  } catch {
    // Storage can be unavailable (private mode); the choice still applies to this session.
  }
  applyPreference(preference, value);
}

export function usePreference<T extends string>(preference: Preference<T>): [T, (value: T) => void] {
  const [value, setValue] = useState(() => readPreference(preference));
  const update = (next: T) => {
    savePreference(preference, next);
    setValue(next);
  };
  return [value, update];
}

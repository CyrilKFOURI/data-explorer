import { describe, expect, it } from "vitest";

import { readPreference, savePreference, themePreference } from "./preferences";

describe("theme preference", () => {
  it("defaults to following the system", () => {
    expect(readPreference(themePreference)).toBe("system");
    expect(document.documentElement.dataset.theme).toBeUndefined();
  });

  it("persists an explicit choice and mirrors it on <html>", () => {
    savePreference(themePreference, "dark");

    expect(readPreference(themePreference)).toBe("dark");
    expect(document.documentElement.dataset.theme).toBe("dark");
  });

  it("removes the attribute when going back to system", () => {
    savePreference(themePreference, "light");
    savePreference(themePreference, "system");

    expect(document.documentElement.dataset.theme).toBeUndefined();
  });

  it("ignores an unknown stored value", () => {
    localStorage.setItem(themePreference.storageKey, "neon");

    expect(readPreference(themePreference)).toBe("system");
  });
});

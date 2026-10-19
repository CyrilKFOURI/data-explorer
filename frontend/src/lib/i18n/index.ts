import en from "./en.json";

export type MessageKey = keyof typeof en;

const messages: Partial<Record<string, string>> = en;

/** Translate a key, replacing `{name}` placeholders with `vars.name`. A key built at run time
 *  (`ml.option.${value}`) that has no text shows the key itself instead of breaking the page. */
export function t(key: MessageKey, vars: Record<string, string> = {}): string {
  const text = messages[key];
  if (text === undefined) {
    if (import.meta.env.DEV) console.warn(`Missing text for "${key}"`);
    return key;
  }
  return text.replace(/\{(\w+)\}/g, (match, name: string) => vars[name] ?? match);
}

import en from "./en.json";

export type MessageKey = keyof typeof en;

const messages: Record<MessageKey, string> = en;

/** Translate a key, replacing `{name}` placeholders with `vars.name`. */
export function t(key: MessageKey, vars: Record<string, string> = {}): string {
  return messages[key].replace(/\{(\w+)\}/g, (match, name: string) => vars[name] ?? match);
}

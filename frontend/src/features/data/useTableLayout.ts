import { useStoredState } from "../../lib/useStoredState";

/** Hidden and pinned columns of a dataset's table, remembered per dataset in this browser. */
export function useTableLayout(datasetId: string) {
  const [hidden, setHidden] = useStoredState<string[]>(`de.data.${datasetId}.hidden`, []);
  const [pinned, setPinned] = useStoredState<string[]>(`de.data.${datasetId}.pinned`, []);
  const toggle = (list: string[], name: string) =>
    list.includes(name) ? list.filter((item) => item !== name) : [...list, name];
  return {
    hidden,
    pinned,
    setHidden,
    hide: (name: string) => {
      setHidden(toggle(hidden, name));
      if (pinned.includes(name)) setPinned(pinned.filter((item) => item !== name));
    },
    togglePin: (name: string) => setPinned(toggle(pinned, name)),
  };
}

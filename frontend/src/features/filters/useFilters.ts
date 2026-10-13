import { useActiveFilters, useSetFilters, type Condition } from "../../api/filters";

/** Read and change a dataset's filters: add, replace one, remove one, clear. */
export function useFilters(datasetId: string) {
  const conditions = useActiveFilters(datasetId);
  const set = useSetFilters(datasetId);
  return {
    conditions,
    set,
    add: (condition: Condition) => set([...conditions, condition]),
    replace: (index: number, condition: Condition) =>
      set(conditions.map((item, i) => (i === index ? condition : item))),
    remove: (index: number) => set(conditions.filter((_, i) => i !== index)),
    clear: () => set([]),
  };
}

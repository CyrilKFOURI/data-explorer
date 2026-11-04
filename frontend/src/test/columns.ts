/** Column fixtures shaped like the API's ColumnOut. */
export function column(overrides: Record<string, unknown> = {}) {
  return {
    name: "price",
    position: 0,
    storage_dtype: "VARCHAR",
    type: "numeric_continuous",
    role: "amount",
    role_label: "Amount",
    parser: { kind: "number", decimal: ",", format: null, true_values: [], false_values: [] },
    order: null,
    detected_type: "numeric_continuous",
    detected_role: "amount",
    confidence: "high",
    reasons: ["100% of values read as numbers"],
    overridden: false,
    excluded: false,
    summary: {
      rows: 100,
      null_count: 5,
      invalid_count: 0,
      distinct_count: 80,
      examples: ["12.5", "8"],
      histogram: [
        { label: "0", count: 10 },
        { label: "10", count: 30 },
      ],
    },
    ...overrides,
  };
}

export const roles = [
  { id: "amount", label: "Amount" },
  { id: "city", label: "City" },
];

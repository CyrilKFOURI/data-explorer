import { describe as group, expect, it } from "vitest";

import type { Chart } from "../../api/client";
import { validateFilterSearch } from "../../api/filters";
import { choiceOf, choicesFor, describe } from "./conditions";
import { actionsFor } from "./fromChart";

const click = (index: number, customdata: unknown = null) => ({ index, x: null, y: null, customdata, clientX: 0, clientY: 0 });

function chart(overrides: Partial<Chart>): Chart {
  return {
    kind: "bars",
    view: "bars",
    views: ["bars"],
    rows: 100,
    missing: 0,
    distinct: 3,
    bars: [],
    others: null,
    ordered: false,
    bins: [],
    stats: null,
    box: null,
    step: null,
    steps: [],
    examples: [],
    duplicates: 0,
    message: null,
    ...overrides,
  } as Chart;
}

group("filter conditions", () => {
  it("describes conditions in short readable form", () => {
    expect(describe({ column: "country", op: "in", values: ["FR", "BE"], negate: false })).toBe("country ∈ FR, BE");
    expect(describe({ column: "country", op: "in", values: ["FR"], negate: true })).toBe("country ∉ FR");
    expect(describe({ column: "age", op: "gte", value: 30, negate: false })).toBe("age ≥ 30");
    expect(describe({ column: "age", op: "between", low: 1, high: 9, negate: true })).toBe("age outside [1 – 9]");
    expect(describe({ column: "day", op: "part_in", part: "day_of_week", values: ["1", "7"], negate: false })).toBe(
      "day on Mon, Sun",
    );
    expect(describe({ column: "a", op: "in", values: ["1", "2", "3", "4", "5"], negate: false })).toBe("a ∈ 1, 2, 3 +2");
  });

  it("offers the choices that fit the column type", () => {
    const ids = (type: Parameters<typeof choicesFor>[0]) => choicesFor(type).map((choice) => choice.id);

    expect(ids("categorical_nominal")[0]).toBe("in");
    expect(ids("numeric_continuous")).not.toContain("in");
    expect(ids("datetime")).toContain("part_in");
    expect(ids("ignored")).toEqual([]);
    expect(choiceOf({ column: "a", op: "between", negate: true }, "numeric_continuous")?.id).toBe("outside");
  });

  it("keeps only well-formed filters from the URL", () => {
    expect(validateFilterSearch({})).toEqual({});
    expect(validateFilterSearch({ filters: "junk" })).toEqual({});
    const parsed = validateFilterSearch({
      filters: { dataset: "d1", conditions: [{ column: "a", op: "is_null" }, { column: "b", op: "drop" }] },
    });
    expect(parsed.filters?.conditions).toEqual([{ column: "a", op: "is_null", negate: false }]);
  });
});

group("filtering from a chart", () => {
  it("keeps or excludes a clicked category", () => {
    const actions = actionsFor("country", chart({ bars: [{ label: "FR", count: 5 }] }), click(0, ["FR", "5%"]));

    expect(actions.map((action) => action.condition)).toEqual([
      { column: "country", op: "in", values: ["FR"], negate: false },
      { column: "country", op: "in", values: ["FR"], negate: true },
    ]);
  });

  it("filters empty values from the (missing) bar and ignores Others", () => {
    const missing = actionsFor("c", chart({}), click(0, ["(missing)", "1%"]));
    const others = actionsFor("c", chart({}), click(0, ["Others (4)", "9%"]));

    expect(missing[0]?.condition).toEqual({ column: "c", op: "is_null", negate: false });
    expect(others).toEqual([]);
  });

  it("keeps a histogram bin's range", () => {
    const histogram = chart({ kind: "histogram", view: "histogram", bins: [{ start: 0, end: 10, count: 3 }] });

    expect(actionsFor("price", histogram, click(0))[0]?.condition).toEqual({
      column: "price",
      op: "between",
      low: 0,
      high: 10,
      negate: false,
    });
  });

  it("turns a weekday bar into a date part filter", () => {
    const weekdays = chart({ view: "day_of_week", ordered: true, bars: [{ label: "Mon", count: 2 }] });

    expect(actionsFor("signup", weekdays, click(0, ["Mon", "2%"]))[0]?.condition).toEqual({
      column: "signup",
      op: "part_in",
      part: "day_of_week",
      values: ["1"],
      negate: false,
    });
  });
});

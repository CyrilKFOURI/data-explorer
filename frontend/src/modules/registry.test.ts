import { describe, expect, it } from "vitest";

import { modules } from "./registry";

describe("module registry", () => {
  it("has unique ids and paths", () => {
    const ids = modules.map((module) => module.id);
    const paths = modules.map((module) => module.path);

    expect(new Set(ids).size).toBe(ids.length);
    expect(new Set(paths).size).toBe(paths.length);
  });
});

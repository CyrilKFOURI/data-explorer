import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Markdown, parse } from "../../features/help/markdown";
import { appHref, describePage, linkTarget } from "./links";

describe("agent links", () => {
  it("lets links point only inside the app", () => {
    expect(appHref("/d/abc123/variable/Age")).toBe("/d/abc123/variable/Age");
    expect(appHref("/d/abc123/compare?x=Sex&y=Age")).toBe("/d/abc123/compare?x=Sex&y=Age");
    for (const hostile of [
      "https://evil.example/?q=secret",
      "//evil.example",
      "/d//evil.example",
      "/d/abc/\\evil.example",
      "javascript:alert(1)",
      "/d/abc|https://evil.example",
      "/settings",
    ]) {
      expect(appHref(hostile)).toBeNull();
    }
  });

  it("renders outside links as plain text, even inside a table", () => {
    const answer = [
      "See [Age](/d/abc/variable/Age) and [this](https://evil.example/?d=secret).",
      "",
      "| column | link |",
      "|---|---|",
      "| Fare | [go](https://evil.example/x) |",
    ].join("\n");
    render(<Markdown blocks={parse(answer)} href={appHref} />);

    const links = screen.getAllByRole("link");
    expect(links.map((a) => a.getAttribute("href"))).toEqual(["/d/abc/variable/Age"]);
    expect(screen.getByText("go")).toBeInTheDocument();
  });

  it("opens the module pages and downloads reports from the app only", () => {
    expect(linkTarget("d1", { page: "ml", params: { target: "Survived", run: "r1", junk: "x" }, label: "" })).toEqual({
      to: "/d/$datasetId/ml",
      params: { datasetId: "d1" },
      search: { target: "Survived", run: "r1" },
    });
    expect(linkTarget("d1", { page: "report_file", params: { job: "abc123" }, label: "" })).toEqual({
      href: "/api/v1/reports/jobs/abc123/file",
      download: true,
    });
    expect(linkTarget("d1", { page: "report_file", params: { job: "../../x" }, label: "" })).toBeNull();
    expect(linkTarget("d1", { page: "dataset", params: { dataset: "d2" }, label: "" })).toEqual({
      to: "/d/$datasetId",
      params: { datasetId: "d2" },
    });
  });

  it("describes the page the user is on", () => {
    expect(describePage("/d/abc/compare", { x: "Sex", y: "Age" })).toBe("Compare (x = Sex, y = Age)");
    expect(describePage("/d/abc", {})).toBe("Overview");
    expect(describePage("/settings", {})).toBeNull();
  });
});

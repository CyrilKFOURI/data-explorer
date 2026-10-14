import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Markdown, parse, slug } from "./markdown";

const text = `# Guide

Intro with **bold**, *italic* and \`code\`.

## Two words

- first
- second

| Metric | Rule |
|---|---|
| Skewed | \\|skewness\\| > 2 |

## Two words
`;

describe("markdown", () => {
  it("reads headings, paragraphs, lists and tables", () => {
    const blocks = parse(text);

    expect(blocks.map((b) => b.kind)).toEqual(["heading", "paragraph", "heading", "list", "table", "heading"]);
    expect(blocks[2]).toMatchObject({ level: 2, id: "two-words" });
    expect(blocks[5]).toMatchObject({ id: "two-words-1" }); // unique anchors
    expect(blocks[4]).toMatchObject({ header: ["Metric", "Rule"], rows: [["Skewed", "|skewness| > 2"]] });
  });

  it("renders inline styles and table cells", () => {
    render(<Markdown blocks={parse(text)} />);

    expect(screen.getByRole("heading", { level: 1, name: "Guide" })).toBeInTheDocument();
    expect(screen.getByText("bold").tagName).toBe("STRONG");
    expect(screen.getByText("italic").tagName).toBe("EM");
    expect(screen.getByText("code").tagName).toBe("CODE");
    expect(within(screen.getByRole("table")).getByText("|skewness| > 2")).toBeInTheDocument();
  });

  it("makes anchors from titles", () => {
    expect(slug("Relationships between two variables")).toBe("relationships-between-two-variables");
    expect(slug("p-values and *evidence*")).toBe("p-values-and-evidence");
  });
});

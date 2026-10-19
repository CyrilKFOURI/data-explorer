import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { meanColor, RollingControls, span } from "./RollingControls";

const layers = { values: true, mean: true, band: true };

describe("Rolling mean controls", () => {
  it("names each mean in the period's unit and adds a suggested window", () => {
    const onWindows = vi.fn();
    render(
      <RollingControls
        windows={[]}
        auto={7}
        period="week"
        maximum={158}
        align="trailing"
        layers={layers}
        onWindows={onWindows}
        onAlign={vi.fn()}
        onLayers={vi.fn()}
      />,
    );

    expect(screen.getByText("Auto · 7 weeks")).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: "± 1σ band (7 weeks mean)" })).toBeChecked();
    fireEvent.click(screen.getByRole("button", { name: "Add" }));
    fireEvent.click(screen.getByRole("button", { name: "13 weeks" }));
    expect(onWindows).toHaveBeenCalledWith([7, 13]); // the automatic one is kept as the first
  });

  it("removes a mean and switches the window position", () => {
    const onWindows = vi.fn();
    const onAlign = vi.fn();
    render(
      <RollingControls
        windows={[7, 15]}
        auto={null}
        period="day"
        maximum={1000}
        align="trailing"
        layers={layers}
        onWindows={onWindows}
        onAlign={onAlign}
        onLayers={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Remove the 15 days mean" }));
    expect(onWindows).toHaveBeenCalledWith([7]);
    fireEvent.click(screen.getByRole("radio", { name: "Centered" }));
    expect(onAlign).toHaveBeenCalledWith("centered");
  });

  it("matches the chart's colours and spells the span", () => {
    expect(meanColor(0)).toBe("var(--chart-1)");
    expect(meanColor(1)).toBe("var(--chart-3)"); // the figure's palette[2] for the first extra mean
    expect(span(1, "month")).toBe("1 month");
    expect(span(12, "month")).toBe("12 months");
  });
});

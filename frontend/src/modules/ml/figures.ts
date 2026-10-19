import type { Data } from "plotly.js-dist-min";

import type { MlRun } from "../../api/client";
import type { Figure } from "../../charts/Plot";
import { withAlpha } from "../../charts/figures";

type Regression = NonNullable<MlRun["regression"]>;
type Classification = NonNullable<MlRun["classification"]>;
type Coefficient = MlRun["coefficients"][number];

const title = (text: string) => ({ title: { text, font: { size: 11 } } });

/** Predicted against actual, with the line of perfect predictions. */
export function predictedFigure(result: Regression, target: string): Figure {
  return (tokens) => {
    const values = [...result.actual, ...result.predicted];
    const low = Math.min(...values);
    const high = Math.max(...values);
    return {
      data: [
        {
          type: "scattergl",
          mode: "markers",
          x: result.actual,
          y: result.predicted,
          marker: { color: tokens.palette[0] ?? tokens.numeric, size: 5, opacity: 0.55 },
          hovertemplate: "actual %{x:,.4g}<br>predicted %{y:,.4g}<extra></extra>",
        } as Data,
        {
          type: "scatter",
          mode: "lines",
          x: [low, high],
          y: [low, high],
          line: { color: tokens.ink3, dash: "dash", width: 1 },
          hoverinfo: "skip",
        } as Data,
      ],
      layout: { showlegend: false, xaxis: title(`Actual ${target}`), yaxis: title(`Predicted ${target}`) },
    };
  };
}

/** Residuals against predicted values: a funnel shape means the error grows with the value. */
export function residualsFigure(result: Regression): Figure {
  return (tokens) => ({
    data: [
      {
        type: "scattergl",
        mode: "markers",
        x: result.predicted,
        y: result.actual.map((a, i) => a - (result.predicted[i] ?? 0)),
        marker: { color: tokens.palette[0] ?? tokens.numeric, size: 5, opacity: 0.55 },
        hovertemplate: "predicted %{x:,.4g}<br>residual %{y:,.4g}<extra></extra>",
      } as Data,
    ],
    layout: {
      showlegend: false,
      xaxis: title("Predicted"),
      yaxis: { ...title("Actual − predicted"), zeroline: true, zerolinecolor: tokens.ink3 },
    },
  });
}

export function residualHistogram(result: Regression): Figure {
  return (tokens) => ({
    data: [
      {
        type: "bar",
        x: result.residual_bins.map((b) => ((b.start ?? 0) + (b.end ?? 0)) / 2),
        y: result.residual_bins.map((b) => b.count),
        width: result.residual_bins.map((b) => (b.end ?? 0) - (b.start ?? 0)),
        marker: { color: withAlpha(tokens.ink3, 0.5), line: { color: tokens.surface, width: 1 } },
        hovertemplate: "%{x:,.4g}: %{y} rows<extra></extra>",
      } as Data,
    ],
    layout: { showlegend: false, bargap: 0, xaxis: title("Residual"), yaxis: title("Rows") },
  });
}

/** Confusion matrix as a heatmap: counts or % of each actual class (row). */
export function confusionFigure(labels: string[], matrix: number[][], percent: boolean): Figure {
  return (tokens) => {
    const values = matrix.map((row) => {
      const total = row.reduce((a, b) => a + b, 0) || 1;
      return row.map((v) => (percent ? (v / total) * 100 : v));
    });
    return {
      data: [
        {
          type: "heatmap",
          x: labels,
          y: labels,
          z: values,
          text: values.map((row) => row.map((v) => (percent ? `${v.toFixed(0)}%` : String(v)))),
          texttemplate: "%{text}",
          colorscale: [
            [0, tokens.surface],
            [1, tokens.palette[0] ?? tokens.numeric],
          ],
          showscale: false,
          hovertemplate: "actual %{y}<br>predicted %{x}<br>%{text}<extra></extra>",
        } as Data,
      ],
      layout: {
        xaxis: { ...title("Predicted"), type: "category" },
        yaxis: { ...title("Actual"), type: "category", autorange: "reversed" },
      },
    };
  };
}

export function curveFigure(
  x: number[],
  y: number[],
  xTitle: string,
  yTitle: string,
  reference: "diagonal" | "flat" | null,
  flat = 0,
): Figure {
  return (tokens) => {
    const data: Data[] = [
      {
        type: "scatter",
        mode: "lines+markers",
        x,
        y,
        line: { color: tokens.palette[0] ?? tokens.numeric, width: 2 },
        marker: { size: 3 },
        hovertemplate: `${xTitle} %{x:.3f}<br>${yTitle} %{y:.3f}<extra></extra>`,
      } as Data,
    ];
    if (reference) {
      data.push({
        type: "scatter",
        mode: "lines",
        x: [0, 1],
        y: reference === "diagonal" ? [0, 1] : [flat, flat],
        line: { color: tokens.ink3, dash: "dash", width: 1 },
        hoverinfo: "skip",
      } as Data);
    }
    return {
      data,
      layout: {
        showlegend: false,
        xaxis: { ...title(xTitle), range: [0, 1] },
        yaxis: { ...title(yTitle), range: [0, 1.02] },
      },
    };
  };
}

/** The largest coefficients, with their 95 % interval when there is one. */
export function coefficientsFigure(coefficients: Coefficient[]): Figure {
  return (tokens) => {
    const top = coefficients.slice(0, 15).reverse();
    return {
      data: [
        {
          type: "bar",
          orientation: "h",
          y: top.map((c) => c.feature),
          x: top.map((c) => c.estimate),
          error_x:
            top.every((c) => c.low !== null && c.high !== null)
              ? {
                  type: "data",
                  symmetric: false,
                  array: top.map((c) => (c.high ?? c.estimate) - c.estimate),
                  arrayminus: top.map((c) => c.estimate - (c.low ?? c.estimate)),
                  color: tokens.ink3,
                }
              : undefined,
          marker: { color: top.map((c) => (c.estimate >= 0 ? (tokens.palette[0] ?? tokens.numeric) : (tokens.palette[1] ?? tokens.ink2))) },
          hovertemplate: "%{y}: %{x:,.4g}<extra></extra>",
        } as Data,
      ],
      layout: { showlegend: false, margin: { l: 160 }, xaxis: { ...title("Coefficient"), zeroline: true, zerolinecolor: tokens.ink3 } },
    };
  };
}

export type { Classification };

export function importancesFigure(importances: { feature: string; importance: number }[]): Figure {
  return (tokens) => {
    const top = importances.slice(0, 15).reverse();
    return {
      data: [
        {
          type: "bar",
          orientation: "h",
          y: top.map((i) => i.feature),
          x: top.map((i) => i.importance),
          marker: { color: tokens.palette[0] ?? tokens.numeric },
          hovertemplate: "%{y}: %{x:.1%}<extra></extra>",
        } as Data,
      ],
      layout: { showlegend: false, margin: { l: 160 }, xaxis: { ...title("Share of importance"), tickformat: ".0%" } },
    };
  };
}

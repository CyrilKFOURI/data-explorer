import type { Data } from "plotly.js-dist-min";

import type { MlExplanation, MlRun } from "../../api/client";
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

type Explanation = NonNullable<MlExplanation>;
type Shap = NonNullable<Explanation["shap"]>;
type Dependence = Explanation["dependence"][number];
type PermutationItem = NonNullable<Explanation["permutation"]>["items"][number];

/** How much the score drops when each column is shuffled (mean ± sd over 5 repeats). */
export function permutationFigure(items: PermutationItem[], metric: string): Figure {
  return (tokens) => {
    const top = items.slice(0, 15).reverse();
    return {
      data: [
        {
          type: "bar",
          orientation: "h",
          y: top.map((i) => i.column),
          x: top.map((i) => i.mean),
          error_x: { type: "data", array: top.map((i) => i.std), color: tokens.ink3 },
          marker: { color: top.map((i) => (i.mean > 0 ? (tokens.palette[0] ?? tokens.numeric) : tokens.ink3)) },
          hovertemplate: "%{y}: %{x:.4g}<extra></extra>",
        } as Data,
      ],
      layout: {
        showlegend: false,
        margin: { l: 150 },
        xaxis: { ...title(`Drop in ${metric} when shuffled`), zeroline: true, zerolinecolor: tokens.ink3 },
      },
    };
  };
}

/** One line per column, one point per row: where its SHAP value falls, colored by its value. */
export function beeswarmFigure(shap: Shap): Figure {
  return (tokens) => {
    const features = [...shap.features].reverse();
    const low = tokens.palette[0] ?? tokens.numeric;
    const high = tokens.palette[1] ?? tokens.categorical;
    const data: Data[] = features.map((feature, index) => {
      // a fixed jitter, so the swarm does not move between renders
      const jitter = feature.values.map((_, i) => ((((i * 2654435761) >>> 0) % 1000) / 1000 - 0.5) * 0.6);
      const numeric = feature.colors.some((c) => c !== null);
      return {
        type: "scattergl",
        mode: "markers",
        name: feature.column,
        x: feature.values,
        y: jitter.map((j) => index + j),
        marker: numeric
          ? {
              size: 4,
              opacity: 0.75,
              color: feature.colors.map((c) => (c === null ? 0.5 : c)),
              colorscale: [
                [0, low],
                [0.5, tokens.ink3],
                [1, high],
              ],
              cmin: 0,
              cmax: 1,
              showscale: index === features.length - 1,
              colorbar: {
                title: { text: "value", side: "right", font: { size: 10 } },
                tickvals: [0, 1],
                ticktext: ["low", "high"],
                thickness: 8,
                len: 0.5,
              },
            }
          : { size: 4, opacity: 0.6, color: tokens.ink3 },
        hovertemplate: `${feature.column}: %{x:.4g}<extra></extra>`,
      } as Data;
    });
    return {
      data,
      layout: {
        showlegend: false,
        margin: { l: 160 },
        xaxis: { ...title(`SHAP value (${shap.scale})`), zeroline: true, zerolinecolor: tokens.ink3 },
        yaxis: { tickvals: features.map((_, i) => i), ticktext: features.map((f) => f.column), range: [-0.6, features.length - 0.4] },
      },
    };
  };
}

/** The average prediction as one column varies, with how many rows sit at each value below. */
export function dependenceFigure(found: Dependence): Figure {
  return (tokens) => {
    const number = found.kind === "number";
    const curves = Object.entries(found.curves);
    const data: Data[] = curves.map(
      ([name, values], index) =>
        ({
          type: number ? "scatter" : "bar",
          mode: number ? "lines+markers" : undefined,
          name,
          x: found.grid,
          y: values,
          marker: { color: tokens.palette[index % 8], size: 4 },
          line: { color: tokens.palette[index % 8], width: 2 },
          hovertemplate: `${name}: %{y:.4g}<extra>%{x}</extra>`,
        }) as Data,
    );
    data.push({
      type: "bar",
      x: found.grid,
      y: found.counts,
      yaxis: "y2",
      marker: { color: tokens.line },
      hovertemplate: "%{y} rows<extra>%{x}</extra>",
      showlegend: false,
    } as Data);
    return {
      data,
      layout: {
        showlegend: curves.length > 1,
        barmode: "group",
        xaxis: { ...title(found.column), type: number ? "linear" : "category" },
        yaxis: { ...title(found.output), domain: [0.3, 1] },
        yaxis2: { domain: [0, 0.2], showticklabels: false, title: { text: "rows", font: { size: 10 } } },
      },
    };
  };
}

/** From the average prediction to this row's, one contribution at a time. */
export function waterfallFigure(base: number, steps: { label: string; value: number }[], scale: string): Figure {
  return (tokens) => ({
    data: [
      {
        type: "waterfall",
        orientation: "h",
        measure: ["absolute", ...steps.map(() => "relative"), "total"],
        y: ["average", ...steps.map((s) => s.label), "this row"],
        x: [base, ...steps.map((s) => s.value), 0],
        increasing: { marker: { color: tokens.palette[1] ?? tokens.categorical } },
        decreasing: { marker: { color: tokens.palette[0] ?? tokens.numeric } },
        totals: { marker: { color: tokens.ink3 } },
        connector: { line: { color: tokens.line } },
        hovertemplate: "%{y}: %{x:+.4g}<extra></extra>",
      } as Data,
    ],
    layout: {
      showlegend: false,
      margin: { l: 220 },
      yaxis: { autorange: "reversed" },
      xaxis: title(scale === "prediction" ? "Prediction" : `Prediction (${scale})`),
    },
  });
}

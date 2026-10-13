import type { Data, Layout } from "plotly.js-dist-min";
import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";

import { baseLayout, plotConfig, readTokens, type ChartTokens } from "./theme";

type PlotlyModule = typeof import("plotly.js-dist-min");
let plotlyPromise: Promise<PlotlyModule> | null = null;

/** plotly.js is large: load it once, on first use, never in the initial bundle. */
function loadPlotly(): Promise<PlotlyModule> {
  plotlyPromise ??= import("plotly.js-dist-min").then(
    (module) => (module as unknown as { default?: PlotlyModule }).default ?? module,
  );
  return plotlyPromise;
}

/** Bumps when the theme changes (data-theme attribute or system preference). */
function useThemeVersion(): number {
  const [version, setVersion] = useState(0);
  useEffect(() => {
    const bump = () => setVersion((v) => v + 1);
    const observer = new MutationObserver(bump);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    media.addEventListener("change", bump);
    return () => {
      observer.disconnect();
      media.removeEventListener("change", bump);
    };
  }, []);
  return version;
}

export type Figure = (tokens: ChartTokens) => { data: Data[]; layout?: Partial<Layout> };

export type PlotHandle = { toImage: (filename: string) => Promise<void> };

/** The clicked point: its index in its trace, its x / y, and where the click happened. */
export type PointClick = { index: number; x: unknown; y: unknown; customdata: unknown; clientX: number; clientY: number };

type PlotProps = {
  figure: Figure;
  height: number;
  label: string;
  onPointClick?: (point: PointClick) => void;
};

type PlotlyClick = {
  points: { pointIndex?: number; pointNumber?: number; x: unknown; y: unknown; customdata: unknown }[];
  event: MouseEvent;
};
type ClickableElement = HTMLDivElement & {
  on?: (event: string, handler: (data: PlotlyClick) => void) => void;
  removeAllListeners?: (event: string) => void;
};

/** A Plotly chart themed with the design tokens. `figure` builds traces from the tokens. */
export const Plot = forwardRef<PlotHandle, PlotProps>(function Plot({ figure, height, label, onPointClick }, ref) {
  const container = useRef<HTMLDivElement>(null);
  const themeVersion = useThemeVersion();
  const clickHandler = useRef(onPointClick);
  useEffect(() => {
    clickHandler.current = onPointClick;
  });
  const clickable = Boolean(onPointClick);

  useImperativeHandle(ref, () => ({
    toImage: async (filename) => {
      const Plotly = await loadPlotly();
      if (container.current) {
        await Plotly.downloadImage(container.current, { format: "png", filename, width: 1200, height: 700 });
      }
    },
  }));

  useEffect(() => {
    let cancelled = false;
    const element = container.current;
    if (!element) return;
    void loadPlotly().then((Plotly) => {
      if (cancelled) return;
      const tokens = readTokens();
      const { data, layout } = figure(tokens);
      const base = baseLayout(tokens);
      void Plotly.react(
        element,
        data,
        {
          ...base,
          ...layout,
          xaxis: { ...base.xaxis, ...layout?.xaxis },
          yaxis: { ...base.yaxis, ...layout?.yaxis },
          height,
        },
        plotConfig,
      ).then(() => {
        const plot = element as ClickableElement;
        plot.removeAllListeners?.("plotly_click");
        if (!clickable) return;
        plot.on?.("plotly_click", (data) => {
          const point = data.points[0];
          if (!point) return;
          clickHandler.current?.({
            index: point.pointIndex ?? point.pointNumber ?? 0,
            x: point.x,
            y: point.y,
            customdata: point.customdata,
            clientX: data.event.clientX,
            clientY: data.event.clientY,
          });
        });
      });
    });
    return () => {
      cancelled = true;
    };
  }, [figure, height, themeVersion, clickable]);

  useEffect(() => {
    const element = container.current;
    return () => {
      if (element) void loadPlotly().then((Plotly) => Plotly.purge(element));
    };
  }, []);

  return (
    <div
      ref={container}
      role="img"
      aria-label={label}
      style={{ height }}
      className={`w-full ${clickable ? "[&_.cursor-crosshair]:cursor-pointer [&_.nsewdrag]:cursor-pointer" : ""}`}
    />
  );
});

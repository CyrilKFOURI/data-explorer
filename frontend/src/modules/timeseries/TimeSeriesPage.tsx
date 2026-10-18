import { useNavigate, useParams, useSearch } from "@tanstack/react-router";
import { useCallback, useMemo, useState, type ReactNode } from "react";

import type {
  MethodResult,
  SeriesBreaks,
  SeriesResiduals,
  SeriesVolatility,
  SeriesDecomposition,
  SeriesOverview,
  SeriesSeasonality,
} from "../../api/client";
import { useDataset, useSeriesSection } from "../../api/hooks";
import { Plot } from "../../charts/Plot";
import { formatNumber } from "../../charts/figures";
import { NoRows } from "../../features/filters/NoRows";
import { formatCount } from "../../lib/format";
import { t, type MessageKey } from "../../lib/i18n";
import { Checkbox, ErrorNote, Select } from "../../ui/fields";
import { SegmentedControl } from "../../ui/SegmentedControl";
import {
  decompositionFigure,
  overlayFigure,
  overviewFigure,
  profileFigure,
} from "./figures";
import {
  AutocorrelationBody,
  autocorrelationVerdict,
  StationarityBody,
  stationarityVerdict,
  TransformPicker,
  type SeriesAutocorrelation,
  type SeriesStationarity,
} from "./Memory";
import { ForecastSection } from "./Forecast";
import { MethodsRow, MethodsTable, useMethods } from "./Methods";
import {
  BreaksBody,
  breaksVerdict,
  ResidualsBody,
  residualsVerdict,
  VolatilityBody,
  volatilityVerdict,
} from "./Shape";
import {
  AGGREGATES,
  DECOMPOSITIONS,
  GAPS,
  PERIODS,
  seriesParams,
  type TimeSeriesSearch,
} from "./search";

const HORIZON: Record<string, number> = {
  hour: 24,
  day: 30,
  week: 12,
  month: 12,
  quarter: 8,
  year: 3,
};
const WINDOWS = [3, 4, 6, 7, 12, 14, 24, 26, 30, 52, 90];
const SECTIONS = [
  "overview",
  "seasonality",
  "decomposition",
  "stationarity",
  "autocorrelation",
  "volatility",
  "residuals",
  "breaks",
  "forecast",
] as const;
type SectionKey = (typeof SECTIONS)[number];
/** `text` is short (side contents); `detail`, when given, is the full sentence of the section. */
type Verdict = { text: string; tone: "ok" | "none"; detail?: string } | null;

/** Becomes true once the element has been on screen, or a moment after it appears: a hidden or
 *  background tab never reports intersections, and the sections should still fill in. */
function useSeen(
  delay = 2000,
): [(element: HTMLElement | null) => void, boolean] {
  const [seen, setSeen] = useState(typeof IntersectionObserver === "undefined");
  const ref = useCallback(
    (element: HTMLElement | null) => {
      if (!element || seen) return;
      const timer = window.setTimeout(() => setSeen(true), delay);
      const observer = new IntersectionObserver((entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          window.clearTimeout(timer);
          setSeen(true);
          observer.disconnect();
        }
      });
      observer.observe(element);
    },
    [seen, delay],
  );
  return [ref, seen];
}

const periodName = (period: string) => t(`time.period.${period}` as MessageKey);

export function TimeSeriesPage() {
  const { datasetId } = useParams({ strict: false }) as { datasetId: string };
  const search = useSearch({ strict: false }) as TimeSeriesSearch;
  const navigate = useNavigate();
  const dataset = useDataset(datasetId);
  const ready = dataset.data?.status === "ready";
  const params = useMemo(() => seriesParams(search), [search]);
  const set = (patch: Partial<TimeSeriesSearch>) =>
    void navigate({
      to: ".",
      search: (previous: Record<string, unknown>) => ({
        ...previous,
        ...patch,
      }),
      replace: true,
    });

  const [trendMethods, setTrendMethods] = useMethods("trend");
  const [seasonMethods, setSeasonMethods] = useMethods("seasonality");
  const [seasonalityRef, seasonalitySeen] = useSeen();
  const [decompositionRef, decompositionSeen] = useSeen();
  const method = search.method ?? "stl";

  const overview = useSeriesSection<SeriesOverview>(
    datasetId,
    "overview",
    params,
    { methods: trendMethods.join(",") },
    ready,
  );
  const okay = Boolean(overview.data);
  const seasonality = useSeriesSection<SeriesSeasonality>(
    datasetId,
    "seasonality",
    params,
    { methods: seasonMethods.join(",") },
    ready && okay && seasonalitySeen,
  );
  const decomposition = useSeriesSection<SeriesDecomposition>(
    datasetId,
    "decomposition",
    params,
    { method },
    ready && okay && decompositionSeen,
  );

  const [stationarityMethods, setStationarityMethods] =
    useMethods("stationarity");
  const [memoryMethods, setMemoryMethods] = useMethods("autocorrelation");
  const [stationarityRef, stationaritySeen] = useSeen();
  const [memoryRef, memorySeen] = useSeen();
  const transform = search.transform ?? "none";
  const pacf = search.pacf ?? "ywm";
  const stationarity = useSeriesSection<SeriesStationarity>(
    datasetId,
    "stationarity",
    params,
    { transform, methods: stationarityMethods.join(",") },
    ready && okay && stationaritySeen,
  );
  const memory = useSeriesSection<SeriesAutocorrelation>(
    datasetId,
    "autocorrelation",
    params,
    { transform, pacf, methods: memoryMethods.join(",") },
    ready && okay && memorySeen,
  );

  const [volatilityMethods, setVolatilityMethods] = useMethods("volatility");
  const [breakMethods, setBreakMethods] = useMethods("breaks");
  const [volatilityRef, volatilitySeen] = useSeen();
  const [residualsRef, residualsSeen] = useSeen();
  const [breaksRef, breaksSeen] = useSeen();
  const volatility = useSeriesSection<SeriesVolatility>(
    datasetId,
    "volatility",
    params,
    { methods: volatilityMethods.join(",") },
    ready && okay && volatilitySeen,
  );
  const residuals = useSeriesSection<SeriesResiduals>(
    datasetId,
    "residuals",
    params,
    { source: search.rsource ?? "residuals" },
    ready && okay && residualsSeen,
  );
  const breakExtra: Record<string, string> = {
    search: search.segment ?? "pelt",
    cost: search.cost ?? "auto",
    sensitivity: search.sens ?? "medium",
    anomaly: search.anomaly ?? "robust_z",
    threshold: String(search.threshold ?? 3.5),
    methods: breakMethods.join(","),
  };
  const breaks = useSeriesSection<SeriesBreaks>(
    datasetId,
    "breaks",
    params,
    breakExtra,
    ready && okay && breaksSeen,
  );

  const verdicts: Record<SectionKey, Verdict> = {
    overview: overview.data ? trendVerdict(overview.data.methods) : null,
    seasonality: seasonality.data ? seasonalityVerdict(seasonality.data) : null,
    decomposition: decomposition.data
      ? decompositionVerdict(decomposition.data)
      : null,
    stationarity: stationarity.data
      ? stationarityVerdict(stationarity.data)
      : null,
    autocorrelation: memory.data ? autocorrelationVerdict(memory.data) : null,
    volatility: volatility.data ? volatilityVerdict(volatility.data) : null,
    residuals: residuals.data ? residualsVerdict(residuals.data) : null,
    breaks: breaks.data ? breaksVerdict(breaks.data) : null,
    forecast: null,
  };

  return (
    <div className="flex flex-col">
      <header className="px-8 pt-6 pb-3">
        <h1 className="text-xl font-semibold tracking-tight">
          {t("ts.title")}
        </h1>
        <p className="mt-1 max-w-prose text-ink-2">{t("ts.description")}</p>
      </header>

      {overview.isError ? (
        <div className="px-8">
          <ErrorNote>{overview.error.message}</ErrorNote>
        </div>
      ) : !overview.data ? (
        <div
          className="mx-8 h-[420px] animate-pulse rounded-lg bg-surface-1"
          aria-busy="true"
        />
      ) : overview.data.setup.total === 0 ? (
        <div className="px-8">
          <NoRows datasetId={datasetId} />
        </div>
      ) : (
        <>
          <ConfigBar data={overview.data} search={search} onChange={set} />
          <div className="grid gap-6 px-8 py-5 lg:grid-cols-[170px_minmax(0,1fr)]">
            <nav aria-label={t("ts.contents")} className="hidden lg:block">
              <ul className="sticky top-20 space-y-1 text-[13px]">
                {SECTIONS.map((key) => (
                  <li key={key}>
                    <a
                      href={`#ts-${key}`}
                      className="flex items-start gap-2 rounded-md px-2 py-1 text-ink-2 hover:bg-surface-1 hover:text-ink-1"
                    >
                      <span
                        aria-hidden
                        className={`mt-1.5 size-2 shrink-0 rounded-full ${
                          verdicts[key] === null
                            ? "bg-line"
                            : verdicts[key]?.tone === "ok"
                              ? "bg-accent"
                              : "bg-ink-3"
                        }`}
                      />
                      <span>
                        {t(`ts.section.${key}` as MessageKey)}
                        {verdicts[key] && (
                          <span className="block text-xs text-ink-3">
                            {verdicts[key]?.text}
                          </span>
                        )}
                      </span>
                    </a>
                  </li>
                ))}
              </ul>
            </nav>
            <div className="min-w-0 space-y-8">
              <OverviewSection
                data={overview.data}
                search={search}
                onChange={set}
                methods={trendMethods}
                onMethods={setTrendMethods}
              />
              <Section
                id="seasonality"
                sectionRef={seasonalityRef}
                verdict={verdicts.seasonality}
              >
                <MethodsRow
                  section="seasonality"
                  chosen={seasonMethods}
                  onChange={setSeasonMethods}
                />
                <SectionBody query={seasonality}>
                  {(data) => (
                    <SeasonalityBody
                      data={data}
                      what={valueLabel(overview.data)}
                    />
                  )}
                </SectionBody>
              </Section>
              <Section
                id="decomposition"
                sectionRef={decompositionRef}
                verdict={verdicts.decomposition}
              >
                <div className="flex flex-wrap items-center gap-3">
                  <SegmentedControl
                    label={t("ts.decomposition.method")}
                    value={method}
                    options={DECOMPOSITIONS.map((value) => ({
                      value,
                      label: t(`ts.decomposition.${value}` as MessageKey),
                    }))}
                    onChange={(value) =>
                      set({ method: value === "stl" ? undefined : value })
                    }
                  />
                  <label className="flex items-center gap-1.5 text-xs text-ink-2">
                    {t("ts.season")}
                    <Select
                      value={search.season ? String(search.season) : ""}
                      onChange={(event) =>
                        set({
                          season: event.target.value
                            ? Number(event.target.value)
                            : undefined,
                        })
                      }
                      className="h-7 text-xs"
                    >
                      <option value="">
                        {t("time.auto", {
                          value: String(overview.data.setup.season ?? "—"),
                        })}
                      </option>
                      {[4, 6, 7, 12, 24, 52, 168, 365].map((n) => (
                        <option key={n} value={n}>
                          {n}
                        </option>
                      ))}
                    </Select>
                  </label>
                </div>
                <SectionBody query={decomposition}>
                  {(data) => <DecompositionBody data={data} />}
                </SectionBody>
              </Section>
              <Section
                id="stationarity"
                sectionRef={stationarityRef}
                verdict={verdicts.stationarity}
              >
                <TransformPicker
                  value={transform}
                  suggested={stationarity.data?.suggestion?.transform ?? null}
                  onChange={(value) =>
                    set({ transform: value === "none" ? undefined : value })
                  }
                />
                <MethodsRow
                  section="stationarity"
                  chosen={stationarityMethods}
                  onChange={setStationarityMethods}
                />
                <SectionBody query={stationarity}>
                  {(data) => <StationarityBody data={data} />}
                </SectionBody>
              </Section>
              <Section
                id="autocorrelation"
                sectionRef={memoryRef}
                verdict={verdicts.autocorrelation}
              >
                <p className="text-xs text-ink-3">
                  {t("ts.memoryOn", {
                    how: t(
                      `ts.transform.${transform}` as MessageKey,
                    ).toLowerCase(),
                  })}
                </p>
                <MethodsRow
                  section="autocorrelation"
                  chosen={memoryMethods}
                  onChange={setMemoryMethods}
                />
                <SectionBody query={memory}>
                  {(data) => (
                    <AutocorrelationBody
                      data={data}
                      pacf={pacf}
                      onPacf={(value) =>
                        set({
                          pacf:
                            value === "ywm"
                              ? undefined
                              : (value as TimeSeriesSearch["pacf"]),
                        })
                      }
                    />
                  )}
                </SectionBody>
              </Section>
              <Section
                id="volatility"
                sectionRef={volatilityRef}
                verdict={verdicts.volatility}
              >
                <MethodsRow
                  section="volatility"
                  chosen={volatilityMethods}
                  onChange={setVolatilityMethods}
                />
                <SectionBody query={volatility}>
                  {(data) => <VolatilityBody data={data} />}
                </SectionBody>
              </Section>
              <Section
                id="residuals"
                sectionRef={residualsRef}
                verdict={verdicts.residuals}
              >
                <SectionBody query={residuals}>
                  {(data) => (
                    <ResidualsBody
                      data={data}
                      source={search.rsource ?? "residuals"}
                      onChange={set}
                    />
                  )}
                </SectionBody>
              </Section>
              <Section
                id="breaks"
                sectionRef={breaksRef}
                verdict={verdicts.breaks}
              >
                <MethodsRow
                  section="breaks"
                  chosen={breakMethods}
                  onChange={setBreakMethods}
                />
                <SectionBody query={breaks}>
                  {(data) => (
                    <BreaksBody
                      data={data}
                      datasetId={datasetId}
                      search={search}
                      onChange={set}
                    />
                  )}
                </SectionBody>
              </Section>
              <Section id="forecast" verdict={null}>
                <ForecastSection
                  datasetId={datasetId}
                  params={params}
                  period={overview.data.setup.period}
                  what={valueLabel(overview.data)}
                  defaultHorizon={Math.max(
                    1,
                    Math.min(
                      HORIZON[overview.data.setup.period] ?? 12,
                      Math.floor(overview.data.setup.periods / 4),
                    ),
                  )}
                />
              </Section>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function valueLabel(data: SeriesOverview): string {
  return `${t(`time.agg.${data.setup.aggregate}` as MessageKey).toLowerCase()} ${data.setup.value}`;
}

// --- Configuration -------------------------------------------------------------------------------

function ConfigBar({
  data,
  search,
  onChange,
}: {
  data: SeriesOverview;
  search: TimeSeriesSearch;
  onChange: (patch: Partial<TimeSeriesSearch>) => void;
}) {
  const setup = data.setup;
  const pick = (
    label: string,
    value: string,
    options: { value: string; label: string }[],
    patch: (v: string) => Partial<TimeSeriesSearch>,
  ) => (
    <label className="flex items-center gap-1.5">
      <span className="text-ink-3">{label}</span>
      <Select
        value={value}
        onChange={(event) => onChange(patch(event.target.value))}
        className="h-7 text-xs"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </Select>
    </label>
  );
  const none = { value: "", label: t("compare.none") };
  return (
    <div
      className="sticky top-0 z-10 border-y border-line bg-surface-0/95 px-8 py-2 backdrop-blur"
      role="group"
      aria-label={t("ts.config")}
    >
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs">
        {pick(
          t("ts.time"),
          setup.time,
          setup.dates.map((n) => ({ value: n, label: n })),
          (v) => ({ time: v }),
        )}
        {pick(
          t("ts.value"),
          setup.value,
          setup.numbers.map((n) => ({ value: n, label: n })),
          (v) => ({ value: v }),
        )}
        {pick(
          t("time.period"),
          search.period ?? "",
          [
            {
              value: "",
              label: t("time.auto", {
                value: t(`time.periodName.${setup.period}` as MessageKey),
              }),
            },
            ...PERIODS.map((p) => ({
              value: p,
              label: t(`time.periodName.${p}` as MessageKey),
            })),
          ],
          (v) => ({ period: (v || undefined) as TimeSeriesSearch["period"] }),
        )}
        {pick(
          t("time.aggregate"),
          search.agg ?? "",
          [
            {
              value: "",
              label: t("time.auto", {
                value: t(`time.agg.${setup.aggregate}` as MessageKey),
              }),
            },
            ...AGGREGATES.map((a) => ({
              value: a,
              label: t(`time.agg.${a}` as MessageKey),
            })),
          ],
          (v) => ({ agg: (v || undefined) as TimeSeriesSearch["agg"] }),
        )}
        {pick(
          t("ts.group"),
          setup.group ?? "",
          [none, ...setup.categories.map((n) => ({ value: n, label: n }))],
          (v) => ({ group: v || undefined, series: undefined }),
        )}
        {setup.group &&
          pick(
            t("ts.series"),
            setup.series ?? "",
            setup.groups.map((g) => ({ value: g, label: g })),
            (v) => ({ series: v }),
          )}
        {pick(
          t("ts.gaps"),
          setup.gaps,
          GAPS.map((g) => ({
            value: g,
            label: t(`ts.gaps.${g}` as MessageKey),
          })),
          (v) => ({
            gaps: v === "leave" ? undefined : (v as TimeSeriesSearch["gaps"]),
          }),
        )}
      </div>
      <p className="mt-1 text-xs text-ink-3">
        {t("ts.rows", {
          rows: formatCount(setup.rows),
          total: formatCount(setup.total),
          periods: formatCount(setup.periods),
          period: periodName(setup.period),
        })}
        {setup.coarsened
          ? ` · ${t("time.coarsened", { period: periodName(setup.period) })}`
          : ""}
      </p>
    </div>
  );
}

// --- Sections ------------------------------------------------------------------------------------

function Section({
  id,
  sectionRef,
  verdict,
  children,
}: {
  id: SectionKey;
  sectionRef?: (element: HTMLElement | null) => void;
  verdict: Verdict;
  children: ReactNode;
}) {
  return (
    <section
      id={`ts-${id}`}
      ref={sectionRef}
      aria-labelledby={`ts-${id}-title`}
      className="scroll-mt-28 space-y-3"
    >
      <div>
        <h2
          id={`ts-${id}-title`}
          className="text-base font-semibold tracking-tight"
        >
          {t(`ts.section.${id}` as MessageKey)}
        </h2>
        <p className="text-[13px] text-ink-2">
          {t(`ts.section.${id}.question` as MessageKey)}
        </p>
        {verdict && (
          <p
            className={`mt-1 font-medium ${verdict.tone === "ok" ? "text-ink-1" : "text-ink-2"}`}
          >
            {verdict.detail ?? verdict.text}
          </p>
        )}
      </div>
      {children}
    </section>
  );
}

function SectionBody<T>({
  query,
  children,
}: {
  query: { data?: T; isError: boolean; error: Error | null };
  children: (data: T) => ReactNode;
}) {
  if (query.isError) return <ErrorNote>{query.error?.message}</ErrorNote>;
  if (!query.data)
    return (
      <div
        className="h-72 animate-pulse rounded-lg bg-surface-1"
        aria-busy="true"
      />
    );
  return <>{children(query.data)}</>;
}

function OverviewSection({
  data,
  search,
  onChange,
  methods,
  onMethods,
}: {
  data: SeriesOverview;
  search: TimeSeriesSearch;
  onChange: (patch: Partial<TimeSeriesSearch>) => void;
  methods: string[];
  onMethods: (keys: string[]) => void;
}) {
  const [layers, setLayers] = useState({
    values: true,
    mean: true,
    band: true,
  });
  const setup = data.setup;
  const what = valueLabel(data);
  const rolled = data.window
    ? t(data.align === "centered" ? "time.rollingCentered" : "time.rolling", {
        window: String(data.window),
        period: periodName(setup.period),
      }).replace(" ± 1σ", "")
    : "";
  const showAll = Boolean(search.all);
  const figure = useMemo(() => {
    const others = showAll
      ? data.lines.filter((line) => line.label !== data.analyzed.label)
      : [];
    return overviewFigure(
      data.periods,
      data.analyzed,
      others,
      layers,
      what,
      rolled,
    );
  }, [data, showAll, layers, what, rolled]);
  const figures = data.figures;
  const unit = t("ts.perPeriod", { period: periodName(setup.period) });
  return (
    <Section id="overview" verdict={trendVerdict(data.methods)}>
      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Figure
          label={t("ts.figure.span")}
          value={`${figures.start} → ${figures.end}`}
        />
        <Figure
          label={t("ts.figure.periods")}
          value={formatCount(figures.periods)}
        />
        <Figure
          label={t("ts.figure.missing")}
          value={formatCount(figures.missing)}
        />
        <Figure
          label={t("ts.figure.change")}
          value={
            figures.change === null
              ? "—"
              : `${figures.change >= 0 ? "+" : "−"}${Math.abs(figures.change).toFixed(1)} %`
          }
        />
      </dl>
      <div className="rounded-lg border border-line bg-surface-1 p-3">
        <div className="mb-2 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-ink-2">
          {data.window !== null && (
            <>
              <label className="flex items-center gap-1.5">
                {t("time.window")}
                <Select
                  value={search.window ? String(search.window) : ""}
                  onChange={(event) =>
                    onChange({
                      window: event.target.value
                        ? Number(event.target.value)
                        : undefined,
                    })
                  }
                  className="h-7 text-xs"
                >
                  <option value="">
                    {t("time.auto", { value: String(data.window) })}
                  </option>
                  {WINDOWS.filter((w) => w <= setup.periods).map((w) => (
                    <option key={w} value={w}>
                      {w}
                    </option>
                  ))}
                </Select>
              </label>
              <Select
                aria-label={t("time.align")}
                value={data.align}
                onChange={(event) =>
                  onChange({
                    align:
                      event.target.value === "centered"
                        ? "centered"
                        : undefined,
                  })
                }
                className="h-7 text-xs"
              >
                <option value="trailing">{t("time.align.trailing")}</option>
                <option value="centered">{t("time.align.centered")}</option>
              </Select>
              {(["values", "mean", "band"] as const).map((layer) => (
                <Checkbox
                  key={layer}
                  label={t(`time.layer.${layer}` as MessageKey)}
                  checked={layers[layer]}
                  onChange={(event) =>
                    setLayers({ ...layers, [layer]: event.target.checked })
                  }
                />
              ))}
            </>
          )}
          {setup.group && (
            <Checkbox
              label={t("ts.showAll")}
              checked={Boolean(search.all)}
              onChange={(event) =>
                onChange({ all: event.target.checked || undefined })
              }
            />
          )}
        </div>
        <Plot
          figure={figure}
          height={400}
          label={t("ts.overviewChart", { what })}
        />
      </div>
      {data.message ? (
        <p className="text-ink-2">{data.message}</p>
      ) : (
        <>
          <MethodsRow section="trend" chosen={methods} onChange={onMethods} />
          <MethodsTable results={data.methods} unit={unit} />
          {(setup.first_partial || setup.last_partial) &&
            (setup.aggregate === "sum" || setup.aggregate === "count") && (
              <p className="text-xs text-ink-3">
                {t("ts.partial", { period: periodName(setup.period) })}
              </p>
            )}
        </>
      )}
    </Section>
  );
}

function Figure({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-surface-1 px-3 py-2">
      <dt className="text-xs text-ink-3">{label}</dt>
      <dd className="mt-0.5 font-medium text-ink-1 tabular-nums">{value}</dd>
    </div>
  );
}

function SeasonalityBody({
  data,
  what,
}: {
  data: SeriesSeasonality;
  what: string;
}) {
  if (data.message) return <p className="text-ink-2">{data.message}</p>;
  return (
    <div className="space-y-4">
      <div className="grid gap-4 xl:grid-cols-2">
        {data.profiles.map((profile) => (
          <div
            key={profile.key}
            className="rounded-lg border border-line bg-surface-1 p-3"
          >
            <h3 className="text-[13px] font-medium">
              {t(`ts.profile.${profile.key}` as MessageKey)}
            </h3>
            <p className="mb-1 text-xs text-ink-3">
              {profileSentence(profile)}
            </p>
            <Plot
              figure={profileFigure(profile, what)}
              height={260}
              label={t(`ts.profile.${profile.key}` as MessageKey)}
            />
          </div>
        ))}
        {data.overlay && (
          <div className="rounded-lg border border-line bg-surface-1 p-3">
            <h3 className="text-[13px] font-medium">{t("ts.overlay")}</h3>
            <p className="mb-1 text-xs text-ink-3">{t("ts.overlayHint")}</p>
            <Plot
              figure={overlayFigure(data.overlay, what)}
              height={260}
              label={t("ts.overlay")}
            />
          </div>
        )}
      </div>
      <MethodsTable results={data.methods} />
      <p className="text-xs text-ink-3">
        {t("ts.detrended", { how: data.detrend })}
        {data.filled
          ? ` ${t("ts.filled", { count: String(data.filled) })}`
          : ""}
      </p>
    </div>
  );
}

function DecompositionBody({ data }: { data: SeriesDecomposition }) {
  if (!data.result) return <p className="text-ink-2">{data.message}</p>;
  const parts = data.result;
  return (
    <div className="space-y-3">
      <dl className="grid grid-cols-2 gap-3 sm:max-w-md">
        <Figure
          label={t("ts.strength.trend")}
          value={formatNumber(parts.strength_trend)}
        />
        <Figure
          label={t("ts.strength.seasonal")}
          value={formatNumber(parts.strength_seasonal)}
        />
      </dl>
      <div className="rounded-lg border border-line bg-surface-1 p-3">
        <Plot
          figure={decompositionFigure(data.periods, data.observed, parts)}
          height={140 * (3 + parts.seasonal.length)}
          label={t("ts.section.decomposition")}
        />
      </div>
      {[
        ...parts.notes,
        ...(data.filled
          ? [t("ts.filled", { count: String(data.filled) })]
          : []),
      ].map((note) => (
        <p key={note} className="text-xs text-ink-3">
          {note}
        </p>
      ))}
    </div>
  );
}

// --- Verdicts ------------------------------------------------------------------------------------

function trendVerdict(results: MethodResult[]): Verdict {
  const test = results.find(
    (r) => r.p_value !== null && r.significant !== null,
  );
  if (!test) return null;
  if (!test.significant) return { text: t("ts.verdict.noTrend"), tone: "none" };
  const rising = (test.value ?? test.statistic ?? 0) >= 0;
  return {
    text: t(rising ? "ts.verdict.rising" : "ts.verdict.falling"),
    tone: "ok",
  };
}

const capitalize = (text: string) =>
  text.charAt(0).toUpperCase() + text.slice(1);

function strengthWord(epsilon: number | null): string {
  if (epsilon === null) return "";
  return t(
    epsilon >= 0.14 ? "ts.strong" : epsilon >= 0.06 ? "ts.moderate" : "ts.weak",
  );
}

function profileSentence(
  profile: SeriesSeasonality["profiles"][number],
): string {
  const index = profile.labels.indexOf(profile.strongest ?? "");
  const deviation = index >= 0 ? profile.deviation[index] : null;
  if (
    !profile.test.significant ||
    deviation === null ||
    deviation === undefined
  )
    return t("ts.profile.none");
  return t(deviation >= 0 ? "ts.profile.above" : "ts.profile.below", {
    label: profile.strongest ?? "",
    pct: Math.abs(deviation).toFixed(0),
  });
}

function seasonalityVerdict(data: SeriesSeasonality): Verdict {
  const found = data.profiles
    .filter((p) => p.test.significant)
    .sort((a, b) => (b.test.value ?? 0) - (a.test.value ?? 0))[0];
  if (!found)
    return data.message
      ? null
      : { text: t("ts.verdict.noSeason"), tone: "none" };
  return {
    text: capitalize(
      t("ts.verdict.season", {
        strength: strengthWord(found.test.value),
        profile: t(`ts.profile.${found.key}.short` as MessageKey),
      }),
    ),
    tone: "ok",
  };
}

function decompositionVerdict(data: SeriesDecomposition): Verdict {
  const parts = data.result;
  if (
    !parts ||
    parts.strength_trend === null ||
    parts.strength_seasonal === null
  )
    return null;
  const word = (value: number) =>
    t(value >= 0.64 ? "ts.strong" : value >= 0.4 ? "ts.moderate" : "ts.weak");
  return {
    text: t("ts.verdict.strengths", {
      trend: word(parts.strength_trend),
      season: word(parts.strength_seasonal),
    }),
    tone:
      parts.strength_trend >= 0.4 || parts.strength_seasonal >= 0.4
        ? "ok"
        : "none",
  };
}

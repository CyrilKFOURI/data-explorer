import type { components } from "./schema";

type Schemas = components["schemas"];
export type Health = Schemas["HealthOut"];
export type Dataset = Schemas["DatasetOut"];
export type Job = Schemas["JobOut"];
export type Preview = Schemas["Preview"];
export type SourceOptions = Schemas["SourceOptions"];
export type ImportOptions = Schemas["ImportOptions"];
export type CsvOptions = Schemas["CsvOptions"];
export type ImportResponse = Schemas["ImportResponse"];
export type Listing = Schemas["Listing"];
export type Sample = Schemas["SampleOut"];
export type Upload = Schemas["UploadOut"];
export type ColumnInfo = Schemas["ColumnInfo"];
export type Head = Schemas["HeadOut"];
export type Column = Schemas["ColumnOut"];
/** Fields with a server default (like `reset`) are optional when sending a change. */
export type ColumnChange = Partial<Omit<Schemas["ColumnChange"], "name">> & { name: string };
export type AnalysisType = Column["type"];
export type Role = Schemas["RoleOut"];
export type Conversion = Schemas["ConversionOut"];
// Fields with server defaults are always present in responses.
export type Alert = Required<Schemas["Alert"]>;
export type Overview = Omit<Required<Schemas["Overview"]>, "alerts"> & { alerts: Alert[] };
export type Chart = Required<Schemas["Chart"]>;
export type ChartParams = {
  view?: string | null;
  topN?: number;
  full?: boolean;
  step?: string | null;
  bins?: number | null;
};

/** The server sends every field, defaults included: make them all required, deeply. */
type Complete<T> = T extends (infer Item)[]
  ? Complete<Item>[]
  : T extends object
    ? { [K in keyof T]-?: Complete<T[K]> }
    : T;
export type VariableProfile = Complete<Schemas["VariableProfile"]>;
export type NumericProfile = NonNullable<VariableProfile["numeric"]>;
export type Describe = NumericProfile["describe"];
export type Normality = NumericProfile["normality"];
export type NormalityTest = Normality["tests"][number];
export type CategoricalProfile = NonNullable<VariableProfile["categorical"]>;
export type DateProfile = NonNullable<VariableProfile["date"]>;
export type TextProfile = NonNullable<VariableProfile["text"]>;
export type IdentifierProfile = NonNullable<VariableProfile["identifier"]>;
export type Fit = Complete<Schemas["Fit"]>;
export type Law = Fit["laws"][number];
export type Transform = Fit["transforms"][number];
export type Outliers = Complete<Schemas["Outliers"]>;
export type OutlierMethod = Outliers["method"];

function chartQuery(column: string, params: ChartParams): string {
  const query = new URLSearchParams({ column });
  if (params.view) query.set("view", params.view);
  if (params.topN) query.set("top_n", String(params.topN));
  if (params.full) query.set("full", "true");
  if (params.step) query.set("step", params.step);
  if (params.bins) query.set("bins", String(params.bins));
  return query.toString();
}

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { error?: { message?: string }; detail?: unknown };
    if (body.error?.message) return body.error.message;
  } catch {
    // Not JSON: fall back to the status text.
  }
  return `Request failed (${response.status})`;
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    method,
    headers: {
      Accept: "application/json",
      ...(body === undefined ? {} : { "Content-Type": "application/json" }),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) throw new ApiError(response.status, await errorMessage(response));
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  health: () => request<Health>("GET", "/health"),

  datasets: () => request<Dataset[]>("GET", "/datasets"),
  dataset: (id: string) => request<Dataset>("GET", `/datasets/${id}`),
  importDataset: (path: string, name: string | null, options: ImportOptions) =>
    request<ImportResponse>("POST", "/datasets", { path, name, options }),
  renameDataset: (id: string, name: string) =>
    request<Dataset>("PATCH", `/datasets/${id}`, { name }),
  deleteDataset: (id: string) => request<void>("DELETE", `/datasets/${id}`),
  reimportDataset: (id: string) => request<Job>("POST", `/datasets/${id}/reimport`),
  openDataset: (id: string) => request<Dataset>("POST", `/datasets/${id}/open`),
  schema: (id: string) => request<ColumnInfo[]>("GET", `/datasets/${id}/schema`),
  head: (id: string, limit = 20) => request<Head>("GET", `/datasets/${id}/head?limit=${limit}`),

  columns: (id: string) => request<Column[]>("GET", `/datasets/${id}/columns`),
  updateColumns: (id: string, changes: ColumnChange[]) =>
    request<Column[]>("PATCH", `/datasets/${id}/columns`, { changes }),
  detectColumns: (id: string) => request<Column[]>("POST", `/datasets/${id}/columns/detect`),
  conversion: (id: string, column: string, type: AnalysisType) =>
    request<Conversion>(
      "GET",
      `/datasets/${id}/columns/conversion?column=${encodeURIComponent(column)}&type=${type}`,
    ),
  reviewTypes: (id: string) => request<Dataset>("POST", `/datasets/${id}/columns/review`),
  roles: () => request<Role[]>("GET", "/column-roles"),
  overview: (id: string) => request<Overview>("GET", `/datasets/${id}/overview`),
  chart: (id: string, column: string, params: ChartParams) =>
    request<Chart>("GET", `/datasets/${id}/columns/chart?${chartQuery(column, params)}`),
  variable: (id: string, column: string) =>
    request<VariableProfile>("GET", `/datasets/${id}/variable?${new URLSearchParams({ column })}`),
  fit: (id: string, column: string) =>
    request<Fit>("GET", `/datasets/${id}/variable/fit?${new URLSearchParams({ column })}`),
  outliers: (id: string, column: string, method: OutlierMethod) =>
    request<Outliers>(
      "GET",
      `/datasets/${id}/variable/outliers?${new URLSearchParams({ column, method })}`,
    ),

  job: (id: string) => request<Job>("GET", `/jobs/${id}`),

  preview: (path: string, options: SourceOptions) =>
    request<Preview>("POST", "/sources/preview", { path, options }),
  browse: (path: string | null) =>
    request<Listing>("GET", `/browse${path ? `?path=${encodeURIComponent(path)}` : ""}`),
  samples: () => request<Sample[]>("GET", "/samples"),

  upload: async (file: File): Promise<Upload> => {
    const response = await fetch(`/api/v1/uploads?filename=${encodeURIComponent(file.name)}`, {
      method: "PUT",
      body: file,
    });
    if (!response.ok) throw new ApiError(response.status, await errorMessage(response));
    return (await response.json()) as Upload;
  },
};

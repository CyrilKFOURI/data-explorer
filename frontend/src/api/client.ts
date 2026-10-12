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

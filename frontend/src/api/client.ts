import type { components } from "./schema";

export type Health = components["schemas"]["HealthOut"];

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`/api/v1${path}`, { headers: { Accept: "application/json" } });
  if (!response.ok) throw new ApiError(response.status, `GET ${path} failed (${response.status})`);
  return (await response.json()) as T;
}

export const api = {
  health: () => getJson<Health>("/health"),
};

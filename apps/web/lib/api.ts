import type { AnalyticsSummary, ApplicationItem, JobItem } from "@autoapply/shared";

const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, token?: string): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  analytics: (token?: string) => request<AnalyticsSummary>("/api/v1/analytics/summary", token),
  applications: (token?: string) => request<ApplicationItem[]>("/api/v1/applications", token),
  jobs: (token?: string) => request<JobItem[]>("/api/v1/jobs/search", token)
};


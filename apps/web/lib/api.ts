import type {
  AnalyticsSummary,
  ApplicationItem,
  JobItem,
  ProfileResponse,
  ResumeItem,
  TokenPair,
  UserResponse,
} from "@autoapply/shared";

const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(`${apiBase}${path}`, {
    cache: "no-store",
    ...options,
    headers,
  });
  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new Error(body || `API ${response.status}`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  // Auth
  login: (email: string, password: string) =>
    request<TokenPair>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  register: (email: string, password: string, full_name?: string) =>
    request<TokenPair>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    }),
  me: (token: string) => request<UserResponse>("/api/v1/auth/me", {}, token),

  // Analytics
  analytics: (token: string) =>
    request<AnalyticsSummary>("/api/v1/analytics/summary", {}, token),

  // Applications
  applications: (token: string) =>
    request<ApplicationItem[]>("/api/v1/applications", {}, token),
  createApplication: (job_id: string, token: string) =>
    request<ApplicationItem>("/api/v1/applications", {
      method: "POST",
      body: JSON.stringify({ job_id }),
    }, token),

  // Jobs
  jobs: (token: string, q?: string) =>
    request<JobItem[]>(`/api/v1/jobs/search${q ? `?q=${encodeURIComponent(q)}` : ""}`, {}, token),
  discoverJobs: (source: string, query: string, token: string) =>
    request<{ status: string; task_id: string }>(`/api/v1/jobs/discover?source=${source}&query=${encodeURIComponent(query)}`, { method: "POST" }, token),

  // Profile
  profile: (token: string) =>
    request<ProfileResponse>("/api/v1/profiles/me", {}, token),
  upsertProfile: (data: Partial<ProfileResponse> & { skills?: unknown[]; experience?: unknown[]; education?: unknown[]; projects?: unknown[] }, token: string) =>
    request<ProfileResponse>("/api/v1/profiles/me", {
      method: "PUT",
      body: JSON.stringify(data),
    }, token),
  techFields: () => request<string[]>("/api/v1/profiles/fields"),
  techStacks: (field?: string) =>
    request<string[]>(`/api/v1/profiles/tech-stacks${field ? `?field=${encodeURIComponent(field)}` : ""}`),

  // Resumes
  resumes: (token: string) =>
    request<ResumeItem[]>("/api/v1/resumes", {}, token),
  generateResume: (token: string, techStacks?: string[]) => {
    const params = techStacks?.length
      ? "?" + techStacks.map((s) => `tech_stacks=${encodeURIComponent(s)}`).join("&")
      : "";
    return fetch(`${apiBase}/api/v1/resumes/generate${params}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
  },

  // Automation
  automationTasks: (token: string) =>
    request<import("@autoapply/shared").AutomationTask[]>("/api/v1/automation/tasks", {}, token),
  automationTask: (id: string, token: string) =>
    request<import("@autoapply/shared").AutomationTask>(`/api/v1/automation/tasks/${id}`, {}, token),
  approveTask: (id: string, token: string) =>
    request<Record<string, string>>(`/api/v1/automation/tasks/${id}/approve`, { method: "POST" }, token),
  cancelTask: (id: string, token: string) =>
    request<Record<string, string>>(`/api/v1/automation/tasks/${id}/cancel`, { method: "POST" }, token),
  taskScreenshot: (id: string, token: string) =>
    request<{ screenshot: string | null }>(`/api/v1/automation/tasks/${id}/screenshot`, {}, token),

  // Saved searches
  savedSearches: (token: string) =>
    request<import("@autoapply/shared").SavedSearch[]>("/api/v1/searches", {}, token),
  createSavedSearch: (data: Omit<import("@autoapply/shared").SavedSearch, "id" | "is_active" | "last_run_at">, token: string) =>
    request<import("@autoapply/shared").SavedSearch>("/api/v1/searches", { method: "POST", body: JSON.stringify(data) }, token),
  deleteSavedSearch: (id: string, token: string) =>
    request<void>(`/api/v1/searches/${id}`, { method: "DELETE" }, token),
  runSavedSearch: (id: string, token: string) =>
    request<Record<string, string>>(`/api/v1/searches/${id}/run`, { method: "POST" }, token),

  // Export
  exportApplications: (format: "csv" | "json", token: string) =>
    fetch(`${apiBase}/api/v1/applications/export?format=${format}`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    }),
  optimizeResume: (job_id: string, token: string) =>
    request<Record<string, unknown>>("/api/v1/ai/optimize-resume", {
      method: "POST",
      body: JSON.stringify({ job_id }),
    }, token),
  coverLetter: (job_id: string, token: string) =>
    request<Record<string, unknown>>("/api/v1/ai/cover-letter", {
      method: "POST",
      body: JSON.stringify({ job_id }),
    }, token),
  answerQuestion: (question: string, token: string) =>
    request<Record<string, unknown>>("/api/v1/ai/answer-question", {
      method: "POST",
      body: JSON.stringify({ question }),
    }, token),

  // AI — Phase 2
  atsScore: (job_id: string, token: string) =>
    request<Record<string, unknown>>("/api/v1/ai/ats-score", {
      method: "POST",
      body: JSON.stringify({ job_id }),
    }, token),
  companyResearch: (job_id: string, token: string) =>
    request<Record<string, unknown>>("/api/v1/ai/company-research", {
      method: "POST",
      body: JSON.stringify({ job_id }),
    }, token),
  salaryEstimate: (job_id: string, token: string) =>
    request<Record<string, unknown>>("/api/v1/ai/salary-estimate", {
      method: "POST",
      body: JSON.stringify({ job_id }),
    }, token),
  interviewPrep: (job_id: string, token: string) =>
    request<Record<string, unknown>>("/api/v1/ai/interview-prep", {
      method: "POST",
      body: JSON.stringify({ job_id }),
    }, token),
  semanticJobs: (token: string, limit = 20) =>
    request<import("@autoapply/shared").JobItem[]>(`/api/v1/ai/semantic-jobs?limit=${limit}`, {}, token),
  jobDetail: (job_id: string, token: string) =>
    request<import("@autoapply/shared").JobDetail>(`/api/v1/jobs/${job_id}`, {}, token),
};


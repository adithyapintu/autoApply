export type AnalyticsSummary = {
  applications_this_week: number;
  applications_this_month: number;
  interview_rate: number;
  response_rate: number;
  offer_rate: number;
  average_match_score: number;
};

export type JobItem = {
  id: string;
  title: string;
  source: string;
  location?: string | null;
  url: string;
};

export type ApplicationItem = {
  id: string;
  status: string;
  job_id: string;
};

export type MatchReport = {
  overall_score: number;
  reasons: string[];
  missing_skills: string[];
  strengths: string[];
  recommendation: "apply" | "review" | "skip";
};

export type AutomationCheckpoint = {
  task_id: string;
  status: "awaiting_approval";
  summary: Record<string, unknown>;
  screenshot_url?: string;
};


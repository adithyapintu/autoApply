export type AnalyticsSummary = {
  applications_this_week: number;
  applications_this_month: number;
  interview_rate: number;
  response_rate: number;
  offer_rate: number;
  average_match_score: number;
};

export type FunnelStage = { stage: string; count: number };

export type FunnelData = {
  stages: FunnelStage[];
  total: number;
  median_days_to_response: number | null;
  match_score_correlation: {
    high_score_response_rate: number;
    low_score_response_rate: number;
    high_score_count: number;
    low_score_count: number;
  };
};

export type SourceRow = {
  source: string;
  total: number;
  response_rate: number;
  interview_rate: number;
  offer_rate: number;
  avg_match_score: number | null;
};

export type VelocityData = {
  daily: { date: string; count: number }[];
  rolling_7day_avg: number;
  total_last_30_days: number;
  suggested_monthly_target: number;
  warnings: string[];
};

export type BackgroundTask = {
  id: string;
  celery_task_id: string;
  task_name: string;
  label: string;
  status: "pending" | "running" | "retrying" | "success" | "failed" | "cancelled" | "unknown";
  params: Record<string, string | null>;
  result: Record<string, unknown> | null;
  error: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type MarketSkill = { skill: string; demand: number; in_profile: boolean };

export type MarketData = {
  top_skills: MarketSkill[];
  total_jobs_analyzed: number;
  profile_skill_count: number;
};

export type JobItem = {
  id: string;
  title: string;
  source: string;
  location?: string | null;
  remote_policy?: string | null;
  employment_type?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
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

export type AutomationTask = {
  id: string;
  application_id: string;
  status: "pending" | "running" | "awaiting_approval" | "approved" | "submitted" | "failed" | "cancelled";
  site_adapter: string;
  checkpoint: Record<string, unknown> | null;
  screenshots: string[];
  error: string | null;
};

export type SavedSearch = {
  id: string;
  name: string;
  source: string;
  query: string;
  location: string | null;
  remote_only: boolean;
  salary_min: number | null;
  score_threshold: number;
  interval_hours: number;
  is_active: boolean;
  last_run_at: string | null;
};

export type TokenPair = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type UserResponse = {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  is_email_verified: boolean;
};

export type SkillItem = {
  name: string;
  category: string;
  proficiency?: string | null;
  years?: number | null;
};

export type ProfileResponse = {
  id: string;
  user_id: string;
  years_experience?: number | null;
  seniority?: string | null;
  field?: string | null;
  tech_stacks: string[];
  domain_expertise: string[];
  preferred_roles: string[];
  industries: string[];
  ats_keywords: string[];
  location_preferences: Record<string, unknown>;
  work_authorization: Record<string, unknown>;
  summary?: string | null;
  skills: SkillItem[];
};

export type JobDetail = JobItem & {
  description: string;
  employment_type?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
  visa_sponsorship?: boolean | null;
  company?: string | null;
  company_summary?: string | null;
  has_embedding: boolean;
};

export type ResumeItem = {
  id: string;
  file_name: string;
  parsed_json: Record<string, unknown> | null;
  created_at?: string | null;
};

export type ATSResult = {
  ats_score: number;
  breakdown: {
    keyword_match: number;
    skills_overlap: number;
    action_verbs: number;
    quantified_achievements: number;
    section_completeness: number;
  };
  sections_present: Record<string, boolean>;
  missing_keywords: string[];
  suggestions: string[];
};

export type SalaryEstimate = {
  min_usd: number;
  max_usd: number;
  median_usd: number;
  currency: string;
  confidence: "low" | "medium" | "high";
  reasoning: string;
  equity_note?: string | null;
};

export type CompanyResearch = {
  overview: string;
  tech_signals: string[];
  company_stage: "startup" | "growth" | "enterprise" | "unknown";
  culture_hints: string[];
  red_flags: string[];
};

export type BehavioralQuestion = {
  question: string;
  theme: string;
  suggested_answer: string | null;
  star_hints: string[];
};

export type TechnicalQuestion = {
  question: string;
  topic: string;
  difficulty: "easy" | "medium" | "hard";
  why_relevant: string;
};

export type InterviewPrep = {
  behavioral_questions: BehavioralQuestion[];
  technical_questions: TechnicalQuestion[];
  company_questions: string[];
  talking_points: string[];
  preparation_tips: string[];
};


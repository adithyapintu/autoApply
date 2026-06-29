"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft, Building2, MapPin, DollarSign, Briefcase,
  BarChart2, Cpu, BookOpen, Loader2
} from "lucide-react";
import { Sidebar } from "@/components/sidebar";
import { api } from "@/lib/api";
import type { JobDetail, ATSResult, SalaryEstimate, CompanyResearch } from "@autoapply/shared";

type Panel = "ats" | "company" | "salary" | null;

function ScoreBar({ score, max = 100 }: { score: number; max?: number }) {
  const pct = Math.min((score / max) * 100, 100);
  const color = pct >= 70 ? "bg-moss" : pct >= 45 ? "bg-amber-400" : "bg-coral";
  return (
    <div className="h-2 w-full rounded-full bg-stone-100">
      <div className={`h-2 rounded-full ${color} transition-all`} style={{ width: `${pct}%` }} />
    </div>
  );
}

function ConfidenceBadge({ level }: { level: string }) {
  const styles = { high: "bg-moss/10 text-moss", medium: "bg-amber-50 text-amber-700", low: "bg-stone-100 text-stone-600" };
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${styles[level as keyof typeof styles] ?? styles.low}`}>
      {level} confidence
    </span>
  );
}

export default function JobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [job, setJob] = useState<JobDetail | null>(null);
  const [activePanel, setActivePanel] = useState<Panel>(null);
  const [ats, setAts] = useState<ATSResult | null>(null);
  const [salary, setSalary] = useState<SalaryEstimate | null>(null);
  const [company, setCompany] = useState<CompanyResearch | null>(null);
  const [loading, setLoading] = useState<Panel | "job">("job");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const t = localStorage.getItem("access_token");
    if (!t) { router.push("/login"); return; }
    setToken(t);
    api.jobDetail(id, t)
      .then(setJob)
      .catch(() => setError("Job not found"))
      .finally(() => setLoading(null));
  }, [id, router]);

  async function loadPanel(panel: Panel) {
    if (!token || !id) return;
    setActivePanel(panel); setError(null); setLoading(panel);
    try {
      if (panel === "ats" && !ats) {
        const res = await api.atsScore(id, token);
        setAts(res as unknown as ATSResult);
      } else if (panel === "salary" && !salary) {
        const res = await api.salaryEstimate(id, token);
        setSalary(res as unknown as SalaryEstimate);
      } else if (panel === "company" && !company) {
        const res = await api.companyResearch(id, token);
        setCompany(res as unknown as CompanyResearch);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setLoading(null);
    }
  }

  async function applyToJob() {
    if (!token || !id) return;
    try {
      await api.createApplication(id, token);
      router.push("/applications");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create application");
    }
  }

  if (loading === "job") {
    return (
      <main className="flex min-h-screen bg-paper">
        <Sidebar />
        <div className="flex flex-1 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-stone-400" />
        </div>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen bg-paper">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center gap-4 border-b border-stone-200 bg-white px-8">
          <Link href="/jobs" className="flex items-center gap-1.5 text-sm text-stone-600 hover:text-ink">
            <ArrowLeft className="h-4 w-4" /> Jobs
          </Link>
          {job && (
            <>
              <span className="text-stone-300">|</span>
              <h1 className="text-sm font-semibold text-ink truncate">{job.title}</h1>
            </>
          )}
          <div className="ml-auto flex gap-2">
            <Link
              href={`/interview-prep?job_id=${id}`}
              className="flex items-center gap-1.5 rounded-md border border-stone-200 px-3 py-2 text-sm text-stone-700 hover:bg-stone-50"
            >
              <BookOpen className="h-4 w-4" /> Interview Prep
            </Link>
            <button
              onClick={applyToJob}
              className="rounded-md bg-moss px-4 py-2 text-sm font-medium text-white hover:bg-moss/90"
            >
              Apply
            </button>
          </div>
        </header>

        {error && (
          <div className="mx-8 mt-4 rounded-md bg-coral/10 border border-coral/30 px-4 py-2 text-sm text-coral">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 gap-6 p-8 lg:grid-cols-3">
          {/* Left: job info */}
          <div className="lg:col-span-2 space-y-6">
            {job && (
              <>
                <section className="rounded-lg border border-stone-200 bg-white p-6">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h2 className="text-xl font-semibold text-ink">{job.title}</h2>
                      {job.company && (
                        <p className="mt-1 flex items-center gap-1.5 text-sm text-stone-600">
                          <Building2 className="h-4 w-4" /> {job.company}
                        </p>
                      )}
                    </div>
                    <span className="shrink-0 rounded-full bg-stone-100 px-2.5 py-1 text-xs text-stone-600 capitalize">
                      {job.source}
                    </span>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-3 text-xs text-stone-500">
                    {job.location && <span className="flex items-center gap-1"><MapPin className="h-3.5 w-3.5" />{job.location}</span>}
                    {job.remote_policy === "remote" && <span className="rounded-full bg-moss/10 px-2 py-0.5 font-medium text-moss">Remote</span>}
                    {job.employment_type && <span className="flex items-center gap-1"><Briefcase className="h-3.5 w-3.5" />{job.employment_type}</span>}
                    {(job.salary_min || job.salary_max) && (
                      <span className="flex items-center gap-1">
                        <DollarSign className="h-3.5 w-3.5" />
                        {job.salary_min && `$${(job.salary_min/1000).toFixed(0)}k`}
                        {job.salary_max && `–$${(job.salary_max/1000).toFixed(0)}k`}
                      </span>
                    )}
                  </div>
                </section>

                <section className="rounded-lg border border-stone-200 bg-white p-6">
                  <h3 className="mb-3 text-sm font-semibold text-stone-500 uppercase">Description</h3>
                  <div className="prose prose-sm max-w-none text-stone-700 whitespace-pre-wrap text-sm leading-relaxed">
                    {job.description}
                  </div>
                </section>
              </>
            )}
          </div>

          {/* Right: AI panels */}
          <div className="space-y-4">
            {/* ATS Score */}
            <div className="rounded-lg border border-stone-200 bg-white overflow-hidden">
              <button
                onClick={() => loadPanel("ats")}
                className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-stone-50"
              >
                <div className="flex items-center gap-2 text-sm font-medium text-ink">
                  <BarChart2 className="h-4 w-4 text-moss" /> ATS Score
                </div>
                {loading === "ats" && <Loader2 className="h-4 w-4 animate-spin text-stone-400" />}
              </button>
              {activePanel === "ats" && ats && (
                <div className="border-t border-stone-100 p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-2xl font-bold text-ink">{ats.ats_score}/100</span>
                    <span className={`text-xs font-medium ${ats.ats_score >= 70 ? "text-moss" : ats.ats_score >= 45 ? "text-amber-600" : "text-coral"}`}>
                      {ats.ats_score >= 70 ? "Strong" : ats.ats_score >= 45 ? "Average" : "Weak"}
                    </span>
                  </div>
                  <ScoreBar score={ats.ats_score} />
                  <div className="space-y-1.5 text-xs">
                    {Object.entries(ats.breakdown).map(([k, v]) => (
                      <div key={k} className="flex justify-between text-stone-600">
                        <span className="capitalize">{k.replace(/_/g, " ")}</span>
                        <span className="font-medium text-ink">{v}</span>
                      </div>
                    ))}
                  </div>
                  {ats.suggestions.length > 0 && (
                    <div className="rounded-md bg-amber-50 p-3">
                      <p className="text-xs font-medium text-amber-800 mb-1">Suggestions</p>
                      <ul className="space-y-1">
                        {ats.suggestions.map((s, i) => (
                          <li key={i} className="text-xs text-amber-700">• {s}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Salary Estimate */}
            <div className="rounded-lg border border-stone-200 bg-white overflow-hidden">
              <button
                onClick={() => loadPanel("salary")}
                className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-stone-50"
              >
                <div className="flex items-center gap-2 text-sm font-medium text-ink">
                  <DollarSign className="h-4 w-4 text-moss" /> Salary Estimate
                </div>
                {loading === "salary" && <Loader2 className="h-4 w-4 animate-spin text-stone-400" />}
              </button>
              {activePanel === "salary" && salary && (
                <div className="border-t border-stone-100 p-4 space-y-2">
                  <div className="flex items-baseline gap-2">
                    <span className="text-xl font-bold text-ink">
                      ${(salary.median_usd / 1000).toFixed(0)}k
                    </span>
                    <span className="text-xs text-stone-500">median</span>
                    <ConfidenceBadge level={salary.confidence} />
                  </div>
                  <p className="text-xs text-stone-500">
                    Range: ${(salary.min_usd / 1000).toFixed(0)}k – ${(salary.max_usd / 1000).toFixed(0)}k {salary.currency}
                  </p>
                  <p className="text-xs text-stone-600 italic">{salary.reasoning}</p>
                  {salary.equity_note && <p className="text-xs text-stone-500">{salary.equity_note}</p>}
                </div>
              )}
            </div>

            {/* Company Research */}
            <div className="rounded-lg border border-stone-200 bg-white overflow-hidden">
              <button
                onClick={() => loadPanel("company")}
                className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-stone-50"
              >
                <div className="flex items-center gap-2 text-sm font-medium text-ink">
                  <Building2 className="h-4 w-4 text-moss" /> Company Research
                </div>
                {loading === "company" && <Loader2 className="h-4 w-4 animate-spin text-stone-400" />}
              </button>
              {activePanel === "company" && company && (
                <div className="border-t border-stone-100 p-4 space-y-3">
                  <p className="text-sm text-stone-700">{company.overview}</p>
                  <div className="flex flex-wrap gap-1.5">
                    {company.tech_signals.map((t) => (
                      <span key={t} className="rounded-full bg-steel/10 px-2 py-0.5 text-xs text-steel">{t}</span>
                    ))}
                  </div>
                  {company.culture_hints.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-stone-500 mb-1">Culture</p>
                      {company.culture_hints.map((h, i) => (
                        <p key={i} className="text-xs text-stone-600">• {h}</p>
                      ))}
                    </div>
                  )}
                  {company.red_flags.length > 0 && (
                    <div className="rounded-md bg-coral/5 border border-coral/20 p-2">
                      <p className="text-xs font-medium text-coral mb-1">Flags to note</p>
                      {company.red_flags.map((f, i) => (
                        <p key={i} className="text-xs text-coral/80">• {f}</p>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Tech signals */}
            <div className="rounded-lg border border-stone-200 bg-white p-4">
              <div className="flex items-center gap-2 text-sm font-medium text-ink mb-3">
                <Cpu className="h-4 w-4 text-steel" /> Quick Links
              </div>
              <div className="space-y-2 text-sm">
                <Link href={`/interview-prep?job_id=${id}`} className="block rounded-md bg-moss/5 px-3 py-2 text-moss hover:bg-moss/10">
                  → Generate Interview Prep
                </Link>
                {job?.url && (
                  <a href={job.url} target="_blank" rel="noopener noreferrer"
                    className="block rounded-md bg-stone-50 px-3 py-2 text-stone-600 hover:bg-stone-100">
                    → View Original Posting
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

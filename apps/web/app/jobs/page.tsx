"use client";
import { useEffect, useState } from "react";
import { Search, RefreshCw } from "lucide-react";
import Link from "next/link";
import { Sidebar } from "@/components/sidebar";
import { api } from "@/lib/api";
import type { JobItem } from "@autoapply/shared";

const SOURCES = [
  { value: "all",            label: "All job boards",      type: "keyword",  placeholder: "e.g. Python developer, remote" },
  { value: "linkedin",       label: "LinkedIn",            type: "keyword",  placeholder: "e.g. Frontend engineer, New York" },
  { value: "indeed",         label: "Indeed",              type: "keyword",  placeholder: "e.g. Data scientist, remote" },
  { value: "naukri",         label: "Naukri",              type: "keyword",  placeholder: "e.g. React developer, Bangalore" },
  { value: "wellfound",      label: "Wellfound",           type: "keyword",  placeholder: "e.g. Founding engineer, Series A" },
  { value: "greenhouse",     label: "Greenhouse",          type: "slug",     placeholder: "e.g. stripe,vercel,linear" },
  { value: "lever",          label: "Lever",               type: "slug",     placeholder: "e.g. netflix,figma,notion" },
  { value: "ashby",          label: "Ashby",               type: "slug",     placeholder: "e.g. brex,retool,ramp" },
  { value: "smartrecruiters",label: "SmartRecruiters",     type: "slug",     placeholder: "e.g. ikea,bosch" },
  { value: "workday",        label: "Workday",             type: "slug",     placeholder: "e.g. microsoft,adobe" },
  { value: "company_pages",  label: "Company career pages",type: "domain",   placeholder: "e.g. stripe.com,notion.so,linear.app" },
];

export default function JobsPage() {
  const [token, setToken] = useState<string | null>(null);
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [discovering, setDiscovering] = useState(false);
  const [discoverSource, setDiscoverSource] = useState("all");
  const [discoverQuery, setDiscoverQuery] = useState("");

  const activeSource = SOURCES.find((s) => s.value === discoverSource) ?? SOURCES[0];
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    const t = localStorage.getItem("access_token");
    setToken(t);
    if (t) loadJobs(t, "");
  }, []);

  async function loadJobs(t: string, q: string) {
    setLoading(true);
    try {
      const data = await api.jobs(t, q);
      setJobs(data);
    } catch {
      setJobs([]);
    } finally {
      setLoading(false);
    }
  }

  async function handleDiscover() {
    if (!token) return;
    setDiscovering(true); setMessage(null);
    try {
      const res = await api.discoverJobs(discoverSource, discoverQuery, token);
      setMessage(`Job discovery queued (task: ${res.task_id}). Results will appear after the worker processes the request.`);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Discovery failed");
    } finally {
      setDiscovering(false);
    }
  }

  async function handleApply(jobId: string) {
    if (!token) return;
    try {
      await api.createApplication(jobId, token);
      setMessage("Application created — view it in Applications.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Failed to create application");
    }
  }

  return (
    <main className="flex min-h-screen bg-paper">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center gap-4 border-b border-stone-200 bg-white px-8">
          <div className="flex flex-1 items-center gap-2 rounded-md border border-stone-200 bg-stone-50 px-3 py-2 max-w-md">
            <Search className="h-4 w-4 text-stone-500 shrink-0" />
            <input
              className="w-full bg-transparent text-sm outline-none"
              placeholder="Search jobs by title or keyword"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && token && loadJobs(token, query)}
            />
          </div>
          <button
            onClick={() => token && loadJobs(token, query)}
            className="rounded-md bg-moss px-4 py-2 text-sm font-medium text-white hover:bg-moss/90"
          >
            Search
          </button>
        </header>

        <div className="space-y-6 p-8">
          {message && (
            <div className="rounded-md bg-moss/10 border border-moss/30 px-4 py-2 text-sm text-moss">
              {message}
            </div>
          )}

          {/* Discover panel */}
          <section className="rounded-lg border border-stone-200 bg-white p-4">
            <h2 className="mb-3 text-sm font-semibold text-ink">Discover Jobs</h2>
            <div className="flex flex-wrap gap-3 items-end">
              <div>
                <label className="mb-1 block text-xs text-stone-500">Source</label>
                <select
                  value={discoverSource}
                  onChange={(e) => setDiscoverSource(e.target.value)}
                  className="rounded-md border border-stone-200 bg-white px-3 py-2 text-sm outline-none focus:border-moss"
                >
                  <optgroup label="Job Boards">
                    {SOURCES.filter((s) => s.type === "keyword").map((s) => (
                      <option key={s.value} value={s.value}>{s.label}</option>
                    ))}
                  </optgroup>
                  <optgroup label="ATS Platforms (company slugs)">
                    {SOURCES.filter((s) => s.type === "slug").map((s) => (
                      <option key={s.value} value={s.value}>{s.label}</option>
                    ))}
                  </optgroup>
                  <optgroup label="Direct">
                    {SOURCES.filter((s) => s.type === "domain").map((s) => (
                      <option key={s.value} value={s.value}>{s.label}</option>
                    ))}
                  </optgroup>
                </select>
              </div>
              <div className="flex-1 min-w-[220px]">
                <label className="mb-1 block text-xs text-stone-500">
                  {activeSource.type === "keyword" && "Keywords / role"}
                  {activeSource.type === "slug" && "Company slug(s) — comma-separated"}
                  {activeSource.type === "domain" && "Company domain(s) — comma-separated"}
                </label>
                <input
                  value={discoverQuery}
                  onChange={(e) => setDiscoverQuery(e.target.value)}
                  placeholder={activeSource.placeholder}
                  className="w-full rounded-md border border-stone-200 px-3 py-2 text-sm outline-none focus:border-moss"
                />
              </div>
              <button
                onClick={handleDiscover}
                disabled={discovering || !token}
                className="flex items-center gap-2 rounded-md bg-steel px-4 py-2 text-sm font-medium text-white hover:bg-steel/90 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${discovering ? "animate-spin" : ""}`} />
                {discovering ? "Queuing…" : "Discover"}
              </button>
            </div>
            {activeSource.type === "domain" && (
              <p className="mt-2 text-xs text-stone-400">
                Auto-detects the ATS (Greenhouse, Lever, or Ashby) used by each company domain.
              </p>
            )}
          </section>

          {/* Job list */}
          <section className="rounded-lg border border-stone-200 bg-white overflow-hidden">
            <div className="border-b border-stone-200 px-4 py-3">
              <h2 className="text-sm font-semibold text-ink">
                {loading ? "Loading…" : `${jobs.length} job${jobs.length !== 1 ? "s" : ""}`}
              </h2>
            </div>
            {jobs.length === 0 && !loading ? (
              <div className="px-4 py-10 text-center text-sm text-stone-500">
                No jobs yet. Use Discover above to pull jobs from job boards.
              </div>
            ) : (
              <div className="divide-y divide-stone-100">
                {jobs.map((job) => (
                  <div key={job.id} className="flex items-start justify-between gap-4 px-4 py-4">
                    <div className="min-w-0">
                      <p className="font-medium text-ink truncate">{job.title}</p>
                      <p className="text-xs text-stone-500 mt-0.5">
                        {job.source}
                        {job.location && ` · ${job.location}`}
                        {job.remote_policy === "remote" && " · Remote"}
                        {job.salary_min && ` · $${(job.salary_min / 1000).toFixed(0)}k`}
                        {job.salary_max && `–$${(job.salary_max / 1000).toFixed(0)}k`}
                      </p>
                    </div>
                    <div className="flex shrink-0 gap-2">
                      <a
                        href={job.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="rounded-md border border-stone-200 px-3 py-1.5 text-xs text-stone-700 hover:bg-stone-50"
                      >
                        View
                      </a>
                      <Link
                        href={`/jobs/${job.id}`}
                        className="rounded-md border border-steel/30 px-3 py-1.5 text-xs text-steel hover:bg-steel/5"
                      >
                        Details
                      </Link>
                      <button
                        onClick={() => handleApply(job.id)}
                        className="rounded-md bg-moss px-3 py-1.5 text-xs font-medium text-white hover:bg-moss/90"
                      >
                        Apply
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}

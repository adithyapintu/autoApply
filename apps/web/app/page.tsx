"use client";
import { useEffect, useState } from "react";
import { Bell, Search, Upload } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/sidebar";
import { StatGrid } from "@/components/stat-grid";
import { api } from "@/lib/api";
import type { AnalyticsSummary, JobItem } from "@autoapply/shared";

const EMPTY_SUMMARY: AnalyticsSummary = {
  applications_this_week: 0,
  applications_this_month: 0,
  interview_rate: 0,
  response_rate: 0,
  offer_rate: 0,
  average_match_score: 0,
};

export default function Home() {
  const router = useRouter();
  const [summary, setSummary] = useState<AnalyticsSummary>(EMPTY_SUMMARY);
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const t = localStorage.getItem("access_token");
    setToken(t);
    if (!t) { router.push("/login"); return; }
    api.analytics(t).then(setSummary).catch(() => {});
    api.jobs(t).then((data) => setJobs(data.slice(0, 5))).catch(() => {});
  }, [router]);

  return (
    <main className="flex min-h-screen bg-paper">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center justify-between border-b border-stone-200 bg-white px-4 md:px-8">
          <div className="flex w-full max-w-xl items-center gap-2 rounded-md border border-stone-200 bg-stone-50 px-3 py-2">
            <Search className="h-4 w-4 text-stone-500" aria-hidden="true" />
            <Link href="/jobs">
              <input className="w-full bg-transparent text-sm outline-none cursor-pointer" placeholder="Search jobs, companies, applications" readOnly />
            </Link>
          </div>
          <div className="ml-4 flex items-center gap-2">
            <Link href="/resumes" className="rounded-md border border-stone-200 bg-white p-2 text-stone-700 hover:bg-stone-50" title="Resumes">
              <Upload className="h-4 w-4" aria-hidden="true" />
            </Link>
            <button className="rounded-md border border-stone-200 bg-white p-2 text-stone-700" title="Notifications">
              <Bell className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        </header>

        <div className="space-y-6 p-4 md:p-8">
          <div>
            <h1 className="text-2xl font-semibold text-ink">Application Operations</h1>
            <p className="mt-1 text-sm text-stone-600">Review matches, approve generated materials, and track outcomes.</p>
          </div>

          <StatGrid summary={summary} />

          <section className="rounded-md border border-stone-200 bg-white">
            <div className="flex items-center justify-between border-b border-stone-200 px-4 py-3">
              <h2 className="text-sm font-semibold text-ink">Recommended Jobs</h2>
              <Link href="/jobs" className="rounded-md bg-moss px-3 py-2 text-sm font-medium text-white hover:bg-moss/90">
                Discover
              </Link>
            </div>
            {jobs.length === 0 ? (
              <div className="px-4 py-8 text-center text-sm text-stone-500">
                No jobs yet.{" "}
                <Link href="/jobs" className="text-moss hover:underline">
                  Discover jobs
                </Link>{" "}
                to get started.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[600px] text-left text-sm">
                  <thead className="bg-stone-50 text-xs uppercase text-stone-500">
                    <tr>
                      <th className="px-4 py-3">Title</th>
                      <th className="px-4 py-3">Source</th>
                      <th className="px-4 py-3">Location</th>
                      <th className="px-4 py-3">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {jobs.map((job) => (
                      <tr key={job.id} className="border-t border-stone-100">
                        <td className="px-4 py-3 font-medium text-ink">{job.title}</td>
                        <td className="px-4 py-3 text-stone-500 capitalize">{job.source}</td>
                        <td className="px-4 py-3 text-stone-600">{job.location ?? "—"}</td>
                        <td className="px-4 py-3">
                          <Link href="/jobs" className="rounded-md border border-stone-300 px-3 py-1.5 text-sm text-ink hover:bg-stone-50">
                            Review
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="rounded-md border border-stone-200 bg-white p-4">
            <h2 className="text-sm font-semibold text-ink">Automation Approval Queue</h2>
            <div className="mt-3 rounded-md border border-dashed border-coral/50 bg-coral/5 p-4 text-sm text-stone-700">
              Prepared applications will appear here for explicit review before the final submit action is enabled.
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}


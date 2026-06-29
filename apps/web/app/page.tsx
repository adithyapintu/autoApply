import { Bell, Search, Upload } from "lucide-react";
import { Sidebar } from "@/components/sidebar";
import { StatGrid } from "@/components/stat-grid";

const summary = {
  applications_this_week: 0,
  applications_this_month: 0,
  interview_rate: 0,
  response_rate: 0,
  offer_rate: 0,
  average_match_score: 0
};

const jobs = [
  { company: "Acme Systems", role: "Backend Engineer", score: 91, missing: "Kubernetes" },
  { company: "Northstar AI", role: "AI Engineer", score: 87, missing: "GraphQL" },
  { company: "LedgerWorks", role: "Platform Engineer", score: 82, missing: "Terraform" }
];

export default function Home() {
  return (
    <main className="flex min-h-screen bg-paper">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center justify-between border-b border-stone-200 bg-white px-4 md:px-8">
          <div className="flex w-full max-w-xl items-center gap-2 rounded-md border border-stone-200 bg-stone-50 px-3 py-2">
            <Search className="h-4 w-4 text-stone-500" aria-hidden="true" />
            <input className="w-full bg-transparent text-sm outline-none" placeholder="Search jobs, companies, applications" />
          </div>
          <div className="ml-4 flex items-center gap-2">
            <button className="rounded-md border border-stone-200 bg-white p-2 text-stone-700" title="Upload resume">
              <Upload className="h-4 w-4" aria-hidden="true" />
            </button>
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
              <button className="rounded-md bg-moss px-3 py-2 text-sm font-medium text-white">Discover</button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[680px] text-left text-sm">
                <thead className="bg-stone-50 text-xs uppercase text-stone-500">
                  <tr>
                    <th className="px-4 py-3">Company</th>
                    <th className="px-4 py-3">Role</th>
                    <th className="px-4 py-3">Score</th>
                    <th className="px-4 py-3">Missing</th>
                    <th className="px-4 py-3">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map((job) => (
                    <tr key={`${job.company}-${job.role}`} className="border-t border-stone-100">
                      <td className="px-4 py-3 font-medium text-ink">{job.company}</td>
                      <td className="px-4 py-3 text-stone-700">{job.role}</td>
                      <td className="px-4 py-3 text-moss">{job.score}</td>
                      <td className="px-4 py-3 text-stone-600">{job.missing}</td>
                      <td className="px-4 py-3">
                        <button className="rounded-md border border-stone-300 px-3 py-1.5 text-sm text-ink">Review</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
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


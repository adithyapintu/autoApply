"use client";
import { useEffect, useState } from "react";
import { Sidebar } from "@/components/sidebar";
import { api } from "@/lib/api";
import type { ApplicationItem } from "@autoapply/shared";

const COLUMNS = [
  { key: "draft", label: "Draft" },
  { key: "applied", label: "Applied" },
  { key: "phone_screen", label: "Phone Screen" },
  { key: "interview", label: "Interview" },
  { key: "offer", label: "Offer" },
  { key: "rejected", label: "Rejected" },
];

export default function ApplicationsPage() {
  const [token, setToken] = useState<string | null>(null);
  const [apps, setApps] = useState<ApplicationItem[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const t = localStorage.getItem("access_token");
    setToken(t);
    if (t) {
      setLoading(true);
      api.applications(t).then(setApps).catch(() => setApps([])).finally(() => setLoading(false));
    }
  }, []);

  const byStatus = (status: string) => apps.filter((a) => a.status === status);

  return (
    <main className="flex min-h-screen bg-paper">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center justify-between border-b border-stone-200 bg-white px-8">
          <h1 className="text-xl font-semibold text-ink">Applications</h1>
          <span className="text-sm text-stone-500">{apps.length} total</span>
        </header>

        <div className="flex-1 overflow-x-auto p-8">
          {loading ? (
            <p className="text-sm text-stone-500">Loading…</p>
          ) : (
            <div className="flex gap-4 min-w-max">
              {COLUMNS.map((col) => {
                const items = byStatus(col.key);
                return (
                  <div key={col.key} className="w-56 shrink-0">
                    <div className="mb-3 flex items-center justify-between">
                      <span className="text-xs font-semibold uppercase text-stone-500">{col.label}</span>
                      <span className="rounded-full bg-stone-100 px-2 py-0.5 text-xs text-stone-600">
                        {items.length}
                      </span>
                    </div>
                    <div className="space-y-2">
                      {items.length === 0 ? (
                        <div className="rounded-md border border-dashed border-stone-200 px-3 py-6 text-center text-xs text-stone-400">
                          Empty
                        </div>
                      ) : (
                        items.map((app) => (
                          <div
                            key={app.id}
                            className="rounded-md border border-stone-200 bg-white p-3 shadow-sm"
                          >
                            <p className="text-xs font-medium text-ink truncate">
                              Job {app.job_id.slice(0, 8)}…
                            </p>
                            <p className="mt-1 text-xs text-stone-500 capitalize">{app.status}</p>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {!token && (
            <div className="text-center py-20 text-sm text-stone-500">
              <a href="/login" className="text-moss hover:underline">Sign in</a> to view your applications.
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

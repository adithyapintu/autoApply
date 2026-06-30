"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle, Clock, Loader2, RefreshCw, XCircle, AlertTriangle } from "lucide-react";
import { Sidebar } from "@/components/sidebar";
import { api } from "@/lib/api";
import type { BackgroundTask as Task } from "@autoapply/shared";

const STATUS_CONFIG: Record<string, { icon: React.ElementType; color: string; label: string }> = {
  pending:          { icon: Clock,         color: "text-stone-400 bg-stone-50 border-stone-200",     label: "Queued"     },
  running:          { icon: Loader2,       color: "text-sky-600 bg-sky-50 border-sky-200",           label: "Running"    },
  retrying:         { icon: RefreshCw,     color: "text-amber-600 bg-amber-50 border-amber-200",     label: "Retrying"   },
  success:          { icon: CheckCircle,   color: "text-moss bg-moss/5 border-moss/30",              label: "Completed"  },
  success_with_err: { icon: AlertTriangle, color: "text-amber-600 bg-amber-50 border-amber-200",     label: "Completed with error" },
  failed:           { icon: XCircle,       color: "text-coral bg-coral/5 border-coral/30",           label: "Failed"     },
  cancelled:        { icon: AlertTriangle, color: "text-stone-400 bg-stone-50 border-stone-200",     label: "Cancelled"  },
  unknown:          { icon: Clock,         color: "text-stone-400 bg-stone-50 border-stone-200",     label: "Unknown"    },
};

function effectiveStatus(task: Task): string {
  if (task.status === "success" && task.result && "error" in task.result) return "success_with_err";
  return task.status;
}

function StatusBadge({ task }: { task: Task }) {
  const key = effectiveStatus(task);
  const cfg = STATUS_CONFIG[key] ?? STATUS_CONFIG.unknown;
  const Icon = cfg.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${cfg.color}`}>
      <Icon className={`h-3 w-3 ${task.status === "running" ? "animate-spin" : ""}`} />
      {cfg.label}
    </span>
  );
}

function ParamsSummary({ task }: { task: Task }) {
  const { params, task_name } = task;
  if (task_name === "discover_jobs") {
    return <span>{params.source ?? "all"}{params.query ? ` · "${params.query}"` : ""}{params.location ? ` · ${params.location}` : ""}</span>;
  }
  if (task_name === "parse_resume") {
    return <span>{params.file_name ?? params.resume_id}</span>;
  }
  if (task_name === "run_automation") {
    return <span>{params.site_adapter} · {params.target_url}</span>;
  }
  const first = Object.entries(params).slice(0, 2).map(([k, v]) => `${k}: ${v}`).join(" · ");
  return <span>{first}</span>;
}

function ResultSummary({ task }: { task: Task }) {
  const appError = task.result && "error" in task.result ? String(task.result.error) : null;

  if (task.status === "failed" && task.error) {
    return <p className="mt-1 text-xs text-coral">{task.error}</p>;
  }
  if (appError) {
    return <p className="mt-1 text-xs text-amber-600">{appError}</p>;
  }
  if (task.status === "success" && task.result) {
    const entries = Object.entries(task.result).filter(([k]) => k !== "user_id").slice(0, 4);
    return (
      <p className="mt-1 text-xs text-stone-500">
        {entries.map(([k, v]) => `${k}: ${v}`).join(" · ")}
      </p>
    );
  }
  return null;
}

export default function TasksPage() {
  const router = useRouter();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const tokenRef = useRef<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = useCallback(async (t: string, showLoading = false) => {
    if (showLoading) setLoading(true);
    try {
      const data = await api.backgroundTasks(t);
      setTasks(data);
      setLastRefresh(new Date());
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const t = localStorage.getItem("access_token");
    if (!t) { router.push("/login"); return; }
    tokenRef.current = t;
    load(t, true);

    // Auto-refresh every 5 s while any task is running/pending
    intervalRef.current = setInterval(() => {
      const hasActive = tasks.some((tk) => ["pending", "running", "retrying"].includes(tk.status));
      if (tokenRef.current && hasActive) load(tokenRef.current);
    }, 5000);

    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Restart interval whenever tasks list changes so we re-evaluate active tasks
  useEffect(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    intervalRef.current = setInterval(() => {
      const hasActive = tasks.some((tk) => ["pending", "running", "retrying"].includes(tk.status));
      if (tokenRef.current && hasActive) load(tokenRef.current);
    }, 5000);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [tasks, load]);

  const grouped = tasks.reduce<Record<string, Task[]>>((acc, t) => {
    const day = t.created_at ? t.created_at.slice(0, 10) : "Unknown";
    (acc[day] ??= []).push(t);
    return acc;
  }, {});

  const activeCount = tasks.filter((t) => ["pending", "running", "retrying"].includes(t.status)).length;

  return (
    <main className="flex min-h-screen bg-paper">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center justify-between border-b border-stone-200 bg-white px-4 md:px-8">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-semibold text-ink">Background Tasks</h1>
            {activeCount > 0 && (
              <span className="flex items-center gap-1 rounded-full bg-sky-100 px-2.5 py-0.5 text-xs font-medium text-sky-700">
                <Loader2 className="h-3 w-3 animate-spin" />
                {activeCount} running
              </span>
            )}
          </div>
          <div className="flex items-center gap-3">
            {lastRefresh && (
              <span className="text-xs text-stone-400">
                Updated {lastRefresh.toLocaleTimeString()}
              </span>
            )}
            <button
              onClick={() => tokenRef.current && load(tokenRef.current, false)}
              className="flex items-center gap-1.5 rounded-md border border-stone-200 px-3 py-1.5 text-xs text-stone-600 hover:bg-stone-50"
            >
              <RefreshCw className="h-3 w-3" /> Refresh
            </button>
          </div>
        </header>

        <div className="p-4 md:p-8">
          {loading ? (
            <div className="flex items-center gap-2 text-sm text-stone-500">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading…
            </div>
          ) : tasks.length === 0 ? (
            <div className="rounded-md border border-stone-200 bg-white px-6 py-12 text-center">
              <p className="text-sm font-medium text-ink">No background tasks yet</p>
              <p className="mt-1 text-xs text-stone-500">
                Tasks appear here when you discover jobs, upload resumes, or trigger automation.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {Object.entries(grouped).map(([day, dayTasks]) => (
                <section key={day}>
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-stone-400">{day}</p>
                  <div className="divide-y divide-stone-100 overflow-hidden rounded-md border border-stone-200 bg-white">
                    {dayTasks.map((task) => (
                      <div key={task.id} className="flex items-start gap-4 px-4 py-3.5">
                        <div className="pt-0.5">
                          <StatusBadge task={task} />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium text-ink">{task.label}</p>
                          <p className="mt-0.5 truncate text-xs text-stone-500">
                            <ParamsSummary task={task} />
                          </p>
                          <ResultSummary task={task} />
                        </div>
                        <div className="shrink-0 text-right">
                          <p className="text-xs text-stone-400">
                            {task.created_at ? new Date(task.created_at).toLocaleTimeString() : "—"}
                          </p>
                          <p className="mt-0.5 font-mono text-[10px] text-stone-300">
                            {task.celery_task_id.slice(0, 8)}…
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

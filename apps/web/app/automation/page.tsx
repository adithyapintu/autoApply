"use client";
import { useEffect, useState } from "react";
import { CheckCircle2, XCircle, Loader2, ShieldCheck, AlertTriangle } from "lucide-react";
import { Sidebar } from "@/components/sidebar";
import { api } from "@/lib/api";
import type { AutomationTask } from "@autoapply/shared";

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-stone-100 text-stone-600",
  running: "bg-blue-50 text-blue-600",
  awaiting_approval: "bg-amber-50 text-amber-700",
  approved: "bg-moss/10 text-moss",
  submitted: "bg-moss/20 text-moss font-semibold",
  failed: "bg-coral/10 text-coral",
  cancelled: "bg-stone-100 text-stone-400",
};

function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs capitalize ${STATUS_STYLES[status] ?? STATUS_STYLES.pending}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}

export default function AutomationPage() {
  const [token, setToken] = useState<string | null>(null);
  const [tasks, setTasks] = useState<AutomationTask[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTask, setActiveTask] = useState<AutomationTask | null>(null);
  const [screenshot, setScreenshot] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    const t = localStorage.getItem("access_token");
    setToken(t);
    if (t) loadTasks(t);
  }, []);

  async function loadTasks(t: string) {
    setLoading(true);
    try {
      const data = await api.automationTasks(t);
      setTasks(data);
    } catch { setTasks([]); }
    finally { setLoading(false); }
  }

  async function openTask(task: AutomationTask) {
    setActiveTask(task);
    setScreenshot(null);
    if (token && task.status === "awaiting_approval") {
      const res = await api.taskScreenshot(task.id, token).catch(() => ({ screenshot: null }));
      setScreenshot(res.screenshot);
    }
  }

  async function approve(taskId: string) {
    if (!token) return;
    setActionLoading(taskId);
    try {
      await api.approveTask(taskId, token);
      setMessage("✓ Application queued for submission.");
      await loadTasks(token);
      setActiveTask(null);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Approval failed");
    } finally { setActionLoading(null); }
  }

  async function cancel(taskId: string) {
    if (!token) return;
    setActionLoading(taskId);
    try {
      await api.cancelTask(taskId, token);
      setMessage("Application cancelled.");
      await loadTasks(token);
      setActiveTask(null);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Cancel failed");
    } finally { setActionLoading(null); }
  }

  return (
    <main className="flex min-h-screen bg-paper">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center justify-between border-b border-stone-200 bg-white px-8">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-moss" />
            <h1 className="text-xl font-semibold text-ink">Automation Queue</h1>
          </div>
          <div className="flex items-center gap-2 rounded-md bg-amber-50 border border-amber-200 px-3 py-1.5 text-xs text-amber-800">
            <AlertTriangle className="h-3.5 w-3.5" />
            Applications pause here before submission — you must approve each one.
          </div>
        </header>

        <div className="flex flex-1 gap-0">
          {/* Task list */}
          <div className="w-80 shrink-0 border-r border-stone-200 bg-white">
            {loading ? (
              <div className="flex items-center justify-center py-10">
                <Loader2 className="h-5 w-5 animate-spin text-stone-400" />
              </div>
            ) : tasks.length === 0 ? (
              <div className="px-4 py-10 text-center text-sm text-stone-500">
                No automation tasks yet. Use the Apply button on a job to start.
              </div>
            ) : (
              <div className="divide-y divide-stone-100">
                {tasks.map((task) => (
                  <button
                    key={task.id}
                    onClick={() => openTask(task)}
                    className={`flex w-full items-center justify-between gap-3 px-4 py-3 text-left hover:bg-stone-50 ${activeTask?.id === task.id ? "bg-stone-50" : ""}`}
                  >
                    <div className="min-w-0">
                      <p className="text-xs font-medium text-ink truncate">
                        {task.site_adapter} · {task.id.slice(0, 8)}…
                      </p>
                    </div>
                    <StatusBadge status={task.status} />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Detail panel */}
          <div className="flex-1 p-8 space-y-6">
            {message && (
              <div className="rounded-md bg-moss/10 border border-moss/30 px-4 py-2 text-sm text-moss">{message}</div>
            )}

            {activeTask ? (
              <>
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-ink capitalize">
                      {activeTask.site_adapter} Application
                    </h2>
                    <p className="text-xs text-stone-500 mt-0.5">Task {activeTask.id}</p>
                  </div>
                  <StatusBadge status={activeTask.status} />
                </div>

                {/* Checkpoint summary */}
                {activeTask.checkpoint && (
                  <section className="rounded-lg border border-stone-200 bg-white p-4">
                    <h3 className="mb-3 text-sm font-semibold text-stone-500 uppercase">Form Summary</h3>
                    <pre className="text-xs text-stone-700 overflow-auto whitespace-pre-wrap">
                      {JSON.stringify(activeTask.checkpoint.summary, null, 2)}
                    </pre>
                  </section>
                )}

                {/* Screenshot */}
                {screenshot && (
                  <section className="rounded-lg border border-stone-200 bg-white overflow-hidden">
                    <div className="border-b border-stone-200 px-4 py-2">
                      <h3 className="text-sm font-semibold text-stone-500">Form Preview (before submission)</h3>
                    </div>
                    <img src={screenshot} alt="Form preview" className="w-full" />
                  </section>
                )}

                {/* Error */}
                {activeTask.error && (
                  <div className="rounded-md bg-coral/10 border border-coral/30 px-4 py-3 text-sm text-coral">
                    {activeTask.error}
                  </div>
                )}

                {/* Actions */}
                {activeTask.status === "awaiting_approval" && (
                  <div className="flex gap-3">
                    <button
                      onClick={() => approve(activeTask.id)}
                      disabled={actionLoading === activeTask.id}
                      className="flex items-center gap-2 rounded-md bg-moss px-5 py-2 text-sm font-medium text-white hover:bg-moss/90 disabled:opacity-50"
                    >
                      <CheckCircle2 className="h-4 w-4" />
                      {actionLoading === activeTask.id ? "Processing…" : "Confirm & Submit"}
                    </button>
                    <button
                      onClick={() => cancel(activeTask.id)}
                      disabled={actionLoading === activeTask.id}
                      className="flex items-center gap-2 rounded-md border border-coral/30 px-5 py-2 text-sm font-medium text-coral hover:bg-coral/5"
                    >
                      <XCircle className="h-4 w-4" /> Cancel
                    </button>
                  </div>
                )}
              </>
            ) : (
              <div className="flex flex-col items-center justify-center py-20 text-center">
                <ShieldCheck className="h-10 w-10 text-stone-200 mb-3" />
                <p className="text-sm text-stone-500">Select a task to review its form preview and approve or cancel.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

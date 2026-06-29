"use client";
import { useEffect, useState } from "react";
import { Plus, Trash2, Play, Bell } from "lucide-react";
import { Sidebar } from "@/components/sidebar";
import { api } from "@/lib/api";
import type { SavedSearch } from "@autoapply/shared";

const SOURCES = ["greenhouse", "lever", "ashby", "smartrecruiters", "workday", "wellfound"];

const EMPTY_FORM = {
  name: "", source: "greenhouse", query: "", location: "",
  remote_only: false, salary_min: "", score_threshold: 60, interval_hours: 24,
};

export default function SavedSearchesPage() {
  const [token, setToken] = useState<string | null>(null);
  const [searches, setSearches] = useState<SavedSearch[]>([]);
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [running, setRunning] = useState<string | null>(null);

  useEffect(() => {
    const t = localStorage.getItem("access_token");
    setToken(t);
    if (t) api.savedSearches(t).then(setSearches).catch(() => {});
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setSaving(true); setMessage(null);
    try {
      const created = await api.createSavedSearch({
        name: form.name, source: form.source, query: form.query,
        location: form.location || null,
        remote_only: form.remote_only,
        salary_min: form.salary_min ? parseInt(String(form.salary_min)) : null,
        score_threshold: form.score_threshold,
        interval_hours: form.interval_hours,
      }, token);
      setSearches([created, ...searches]);
      setForm({ ...EMPTY_FORM });
      setShowForm(false);
      setMessage("Saved search created ✓");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Failed");
    } finally { setSaving(false); }
  }

  async function handleDelete(id: string) {
    if (!token) return;
    await api.deleteSavedSearch(id, token).catch(() => {});
    setSearches(searches.filter(s => s.id !== id));
  }

  async function handleRun(id: string) {
    if (!token) return;
    setRunning(id);
    try {
      const res = await api.runSavedSearch(id, token);
      setMessage(`Discovery queued (task: ${res.task_id})`);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Failed");
    } finally { setRunning(null); }
  }

  return (
    <main className="flex min-h-screen bg-paper">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center justify-between border-b border-stone-200 bg-white px-8">
          <div className="flex items-center gap-2">
            <Bell className="h-5 w-5 text-moss" />
            <h1 className="text-xl font-semibold text-ink">Saved Searches</h1>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-2 rounded-md bg-moss px-4 py-2 text-sm font-medium text-white hover:bg-moss/90"
          >
            <Plus className="h-4 w-4" /> New Search
          </button>
        </header>

        <div className="max-w-3xl space-y-6 p-8">
          {message && <div className="rounded-md bg-moss/10 border border-moss/30 px-4 py-2 text-sm text-moss">{message}</div>}

          {showForm && (
            <form onSubmit={handleCreate} className="rounded-lg border border-stone-200 bg-white p-6 space-y-4">
              <h2 className="text-sm font-semibold text-ink">New Saved Search</h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block text-xs font-medium text-stone-500">Name</label>
                  <input value={form.name} onChange={e => setForm({...form, name: e.target.value})} required
                    className="w-full rounded-md border border-stone-200 px-3 py-2 text-sm outline-none focus:border-moss"
                    placeholder="Backend roles at startups" />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-stone-500">Source</label>
                  <select value={form.source} onChange={e => setForm({...form, source: e.target.value})}
                    className="w-full rounded-md border border-stone-200 bg-white px-3 py-2 text-sm outline-none">
                    {SOURCES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-stone-500">Query / Company slug(s)</label>
                  <input value={form.query} onChange={e => setForm({...form, query: e.target.value})}
                    className="w-full rounded-md border border-stone-200 px-3 py-2 text-sm outline-none focus:border-moss"
                    placeholder="stripe,linear,vercel" />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-stone-500">Location</label>
                  <input value={form.location} onChange={e => setForm({...form, location: e.target.value})}
                    className="w-full rounded-md border border-stone-200 px-3 py-2 text-sm outline-none focus:border-moss"
                    placeholder="San Francisco (optional)" />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-stone-500">Min match score (%)</label>
                  <input type="number" min={0} max={100} value={form.score_threshold}
                    onChange={e => setForm({...form, score_threshold: parseInt(e.target.value)})}
                    className="w-full rounded-md border border-stone-200 px-3 py-2 text-sm outline-none focus:border-moss" />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-stone-500">Check every (hours)</label>
                  <input type="number" min={1} max={168} value={form.interval_hours}
                    onChange={e => setForm({...form, interval_hours: parseInt(e.target.value)})}
                    className="w-full rounded-md border border-stone-200 px-3 py-2 text-sm outline-none focus:border-moss" />
                </div>
              </div>
              <label className="flex items-center gap-2 text-sm text-stone-700 cursor-pointer">
                <input type="checkbox" checked={form.remote_only} onChange={e => setForm({...form, remote_only: e.target.checked})}
                  className="rounded" />
                Remote only
              </label>
              <div className="flex gap-3">
                <button type="submit" disabled={saving}
                  className="rounded-md bg-moss px-4 py-2 text-sm font-medium text-white hover:bg-moss/90 disabled:opacity-50">
                  {saving ? "Saving…" : "Create Search"}
                </button>
                <button type="button" onClick={() => setShowForm(false)}
                  className="rounded-md border border-stone-200 px-4 py-2 text-sm text-stone-700 hover:bg-stone-50">
                  Cancel
                </button>
              </div>
            </form>
          )}

          <section className="rounded-lg border border-stone-200 bg-white overflow-hidden">
            {searches.length === 0 ? (
              <div className="px-4 py-10 text-center text-sm text-stone-500">
                No saved searches yet. Create one to get daily job alerts.
              </div>
            ) : (
              <div className="divide-y divide-stone-100">
                {searches.map(s => (
                  <div key={s.id} className="flex items-start justify-between gap-4 px-4 py-4">
                    <div className="min-w-0">
                      <p className="font-medium text-ink">{s.name}</p>
                      <p className="text-xs text-stone-500 mt-0.5">
                        {s.source} · {s.query || "all"}{s.location && ` · ${s.location}`}
                        {s.remote_only && " · Remote"} · score ≥ {s.score_threshold}%
                        · every {s.interval_hours}h
                      </p>
                      {s.last_run_at && (
                        <p className="text-xs text-stone-400 mt-0.5">Last ran: {new Date(s.last_run_at).toLocaleString()}</p>
                      )}
                    </div>
                    <div className="flex shrink-0 gap-2">
                      <button onClick={() => handleRun(s.id)} disabled={running === s.id}
                        className="flex items-center gap-1.5 rounded-md border border-steel/30 px-3 py-1.5 text-xs text-steel hover:bg-steel/5 disabled:opacity-50">
                        <Play className="h-3 w-3" /> {running === s.id ? "Running…" : "Run now"}
                      </button>
                      <button onClick={() => handleDelete(s.id)}
                        className="rounded-md border border-coral/20 p-1.5 text-coral/70 hover:bg-coral/5">
                        <Trash2 className="h-3.5 w-3.5" />
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

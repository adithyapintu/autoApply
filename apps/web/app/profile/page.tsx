"use client";
import { useEffect, useState } from "react";
import { Sidebar } from "@/components/sidebar";
import { TechStackSelector } from "@/components/tech-stack-selector";
import { api } from "@/lib/api";
import type { ProfileResponse } from "@autoapply/shared";

const SENIORITY_OPTIONS = ["Intern", "Junior", "Mid-level", "Senior", "Staff", "Principal", "Director"];

export default function ProfilePage() {
  const [token, setToken] = useState<string | null>(null);
  const [profile, setProfile] = useState<Partial<ProfileResponse>>({
    tech_stacks: [], domain_expertise: [], preferred_roles: [],
    industries: [], ats_keywords: [], skills: [],
  });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const t = localStorage.getItem("access_token");
    setToken(t);
    if (t) {
      api.profile(t).then(setProfile).catch(() => {});
    }
  }, []);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setSaving(true); setError(null);
    try {
      const updated = await api.upsertProfile(profile, token);
      setProfile(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  function set<K extends keyof ProfileResponse>(key: K, value: ProfileResponse[K]) {
    setProfile((p) => ({ ...p, [key]: value }));
  }

  return (
    <main className="flex min-h-screen bg-paper">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center justify-between border-b border-stone-200 bg-white px-8">
          <h1 className="text-xl font-semibold text-ink">Profile</h1>
          {!token && (
            <a href="/login" className="text-sm text-moss hover:underline">Sign in to save</a>
          )}
        </header>

        <form onSubmit={handleSave} className="max-w-3xl space-y-8 p-8">
          {error && <div className="rounded-md bg-coral/10 border border-coral/30 px-3 py-2 text-sm text-coral">{error}</div>}
          {saved && <div className="rounded-md bg-moss/10 border border-moss/30 px-3 py-2 text-sm text-moss">Profile saved ✓</div>}

          {/* Basic Info */}
          <section className="rounded-lg border border-stone-200 bg-white p-6 space-y-4">
            <h2 className="text-sm font-semibold uppercase text-stone-500">Basic Info</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-ink">Years of Experience</label>
                <input
                  type="number" step="0.5" min="0"
                  value={profile.years_experience ?? ""}
                  onChange={(e) => set("years_experience", parseFloat(e.target.value) || undefined)}
                  className="w-full rounded-md border border-stone-200 px-3 py-2 text-sm outline-none focus:border-moss"
                  placeholder="3.5"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-ink">Seniority</label>
                <select
                  value={profile.seniority ?? ""}
                  onChange={(e) => set("seniority", e.target.value || undefined)}
                  className="w-full rounded-md border border-stone-200 bg-white px-3 py-2 text-sm outline-none focus:border-moss"
                >
                  <option value="">Select…</option>
                  {SENIORITY_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-ink">Professional Summary</label>
              <textarea
                rows={3}
                value={profile.summary ?? ""}
                onChange={(e) => set("summary", e.target.value || undefined)}
                className="w-full rounded-md border border-stone-200 px-3 py-2 text-sm outline-none focus:border-moss resize-none"
                placeholder="Brief overview of your background and goals…"
              />
            </div>
          </section>

          {/* Tech Stack */}
          <section className="rounded-lg border border-stone-200 bg-white p-6">
            <h2 className="mb-4 text-sm font-semibold uppercase text-stone-500">Tech Stack & Field</h2>
            <TechStackSelector
              selectedField={profile.field ?? ""}
              selectedStacks={profile.tech_stacks ?? []}
              onFieldChange={(f) => set("field", f || undefined)}
              onStacksChange={(stacks) => set("tech_stacks", stacks)}
            />
          </section>

          {/* Preferences */}
          <section className="rounded-lg border border-stone-200 bg-white p-6 space-y-4">
            <h2 className="text-sm font-semibold uppercase text-stone-500">Job Preferences</h2>
            {(["preferred_roles", "industries", "ats_keywords"] as const).map((key) => (
              <div key={key}>
                <label className="mb-1 block text-sm font-medium text-ink capitalize">
                  {key.replace(/_/g, " ")}
                </label>
                <input
                  type="text"
                  value={(profile[key] as string[])?.join(", ") ?? ""}
                  onChange={(e) =>
                    set(key, e.target.value.split(",").map((s) => s.trim()).filter(Boolean) as never)
                  }
                  className="w-full rounded-md border border-stone-200 px-3 py-2 text-sm outline-none focus:border-moss"
                  placeholder="Comma-separated values"
                />
              </div>
            ))}
          </section>

          <button
            type="submit"
            disabled={saving || !token}
            className="rounded-md bg-moss px-6 py-2 text-sm font-medium text-white hover:bg-moss/90 disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save Profile"}
          </button>
        </form>
      </div>
    </main>
  );
}

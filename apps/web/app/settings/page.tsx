"use client";
import { useEffect, useState } from "react";
import { Download, Shield, User, Loader2 } from "lucide-react";
import { Sidebar } from "@/components/sidebar";
import { api } from "@/lib/api";
import type { UserResponse } from "@autoapply/shared";

export default function SettingsPage() {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<UserResponse | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    const t = localStorage.getItem("access_token");
    setToken(t);
    if (t) api.me(t).then(setUser).catch(() => {});
  }, []);

  async function handleExport(format: "csv" | "json") {
    if (!token) return;
    setDownloading(format); setMessage(null);
    try {
      const res = await api.exportApplications(format, token);
      if (!res.ok) throw new Error(await res.text());
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = format === "csv" ? "applications.csv" : "autoapply-export.json";
      a.click();
      URL.revokeObjectURL(url);
      setMessage(`${format.toUpperCase()} export downloaded ✓`);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Export failed");
    } finally { setDownloading(null); }
  }

  function handleLogout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "/login";
  }

  return (
    <main className="flex min-h-screen bg-paper">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center border-b border-stone-200 bg-white px-8">
          <h1 className="text-xl font-semibold text-ink">Settings</h1>
        </header>

        <div className="max-w-2xl space-y-6 p-8">
          {message && (
            <div className="rounded-md bg-moss/10 border border-moss/30 px-4 py-2 text-sm text-moss">{message}</div>
          )}

          {/* Account */}
          <section className="rounded-lg border border-stone-200 bg-white p-6 space-y-4">
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-steel" />
              <h2 className="text-sm font-semibold text-ink">Account</h2>
            </div>
            {user ? (
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-stone-500">Email</span>
                  <span className="text-ink">{user.email}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-stone-500">Name</span>
                  <span className="text-ink">{user.full_name ?? "—"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-stone-500">Role</span>
                  <span className="text-ink capitalize">{user.role}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-stone-500">Email verified</span>
                  <span className={user.is_email_verified ? "text-moss" : "text-coral"}>
                    {user.is_email_verified ? "Yes" : "No"}
                  </span>
                </div>
              </div>
            ) : (
              <Loader2 className="h-4 w-4 animate-spin text-stone-400" />
            )}
            <button
              onClick={handleLogout}
              className="rounded-md border border-coral/30 px-4 py-2 text-sm text-coral hover:bg-coral/5"
            >
              Sign out
            </button>
          </section>

          {/* Data Export */}
          <section className="rounded-lg border border-stone-200 bg-white p-6 space-y-4">
            <div className="flex items-center gap-2">
              <Download className="h-4 w-4 text-steel" />
              <h2 className="text-sm font-semibold text-ink">Data Export</h2>
            </div>
            <p className="text-sm text-stone-600">
              Download your application history or a complete GDPR data bundle.
            </p>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => handleExport("csv")}
                disabled={downloading !== null || !token}
                className="flex items-center gap-2 rounded-md border border-stone-200 bg-white px-4 py-2 text-sm text-stone-700 hover:bg-stone-50 disabled:opacity-50"
              >
                {downloading === "csv" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
                Applications CSV
              </button>
              <button
                onClick={() => handleExport("json")}
                disabled={downloading !== null || !token}
                className="flex items-center gap-2 rounded-md border border-stone-200 bg-white px-4 py-2 text-sm text-stone-700 hover:bg-stone-50 disabled:opacity-50"
              >
                {downloading === "json" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
                Full Data Export (JSON)
              </button>
            </div>
          </section>

          {/* Privacy */}
          <section className="rounded-lg border border-stone-200 bg-white p-6 space-y-3">
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-steel" />
              <h2 className="text-sm font-semibold text-ink">Privacy & Safety</h2>
            </div>
            <ul className="space-y-2 text-sm text-stone-600">
              <li>• AutoApply never submits an application without your explicit approval.</li>
              <li>• AI generation uses only facts from your profile — no fabrication.</li>
              <li>• Your resume files are stored encrypted and never shared with third parties.</li>
              <li>• All automation screenshots are stored locally and can be exported above.</li>
            </ul>
          </section>
        </div>
      </div>
    </main>
  );
}

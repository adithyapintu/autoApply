"use client";
import { useEffect, useRef, useState } from "react";
import { Download, FileText, Trash2, Upload, Wand2 } from "lucide-react";
import { Sidebar } from "@/components/sidebar";
import { TechStackSelector } from "@/components/tech-stack-selector";
import { api } from "@/lib/api";
import type { ResumeItem } from "@autoapply/shared";

export default function ResumesPage() {
  const [token, setToken] = useState<string | null>(null);
  const [resumes, setResumes] = useState<ResumeItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [genStacks, setGenStacks] = useState<string[]>([]);
  const [genField, setGenField] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const t = localStorage.getItem("access_token");
    setToken(t);
    if (t) api.resumes(t).then(setResumes).catch(() => {});
  }, []);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !token) return;
    setUploading(true); setMessage(null);
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1/resumes`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      });
      if (!res.ok) throw new Error(await res.text());
      setMessage("Resume uploaded — AI parsing queued (check Tasks for status)");
      const updated = await api.resumes(token);
      setResumes(updated);
      setTimeout(() => setMessage(null), 6000);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function handleDelete(id: string) {
    if (!token) return;
    setDeletingId(id);
    try {
      await api.deleteResume(id, token);
      setResumes((prev) => prev.filter((r) => r.id !== id));
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Delete failed");
    } finally {
      setDeletingId(null);
    }
  }

  async function handleGenerate() {
    if (!token) return;
    setGenerating(true); setMessage(null);
    try {
      const res = await api.generateResume(token, genStacks);
      if (!res.ok) throw new Error(await res.text());
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = "resume.pdf"; a.click();
      URL.revokeObjectURL(url);
      setMessage("Resume PDF downloaded ✓");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <main className="flex min-h-screen bg-paper">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center justify-between border-b border-stone-200 bg-white px-8">
          <h1 className="text-xl font-semibold text-ink">Resumes</h1>
          <div className="flex gap-2">
            <input ref={fileRef} type="file" accept=".pdf,.docx" className="hidden" onChange={handleUpload} />
            <button
              onClick={() => fileRef.current?.click()}
              disabled={uploading || !token}
              className="flex items-center gap-2 rounded-md border border-stone-200 bg-white px-3 py-2 text-sm text-stone-700 hover:bg-stone-50 disabled:opacity-50"
            >
              <Upload className="h-4 w-4" />
              {uploading ? "Uploading…" : "Upload Resume"}
            </button>
          </div>
        </header>

        <div className="max-w-3xl space-y-6 p-8">
          {message && (
            <div className="rounded-md bg-moss/10 border border-moss/30 px-4 py-2 text-sm text-moss">{message}</div>
          )}

          <section className="rounded-lg border border-stone-200 bg-white p-6 space-y-4">
            <div className="flex items-center gap-2">
              <Wand2 className="h-4 w-4 text-moss" />
              <h2 className="text-sm font-semibold text-ink">Generate from Profile</h2>
            </div>
            <p className="text-xs text-stone-500">
              Generates a LaTeX-compiled PDF tailored to your selected tech stack. Your profile must be saved first.
            </p>
            <TechStackSelector selectedField={genField} selectedStacks={genStacks} onFieldChange={setGenField} onStacksChange={setGenStacks} />
            <button
              onClick={handleGenerate}
              disabled={generating || !token}
              className="flex items-center gap-2 rounded-md bg-moss px-5 py-2 text-sm font-medium text-white hover:bg-moss/90 disabled:opacity-50"
            >
              <Download className="h-4 w-4" />
              {generating ? "Generating…" : "Download PDF"}
            </button>
          </section>

          <section className="rounded-lg border border-stone-200 bg-white overflow-hidden">
            <div className="border-b border-stone-200 px-4 py-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-ink">Uploaded Resumes</h2>
              {resumes.length > 0 && <span className="text-xs text-stone-400">{resumes.length}</span>}
            </div>
            {resumes.length === 0 ? (
              <div className="px-4 py-8 text-center text-sm text-stone-500">No resumes uploaded yet.</div>
            ) : (
              <div className="divide-y divide-stone-100">
                {resumes.map((r) => {
                  const pj = r.parsed_json as Record<string, unknown> | null;
                  const aiParsed = pj && !("raw_text" in pj) && Object.keys(pj).length > 0;
                  const pending = !pj || (pj && Object.keys(pj).length === 1 && "raw_text" in pj);
                  return (
                    <div key={r.id} className="flex items-center gap-3 px-4 py-3">
                      <FileText className="h-4 w-4 text-steel shrink-0" />
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-ink truncate">{r.file_name}</p>
                        <p className="text-xs text-stone-500">
                          {aiParsed ? (
                            <span className="text-moss">✓ AI parsed</span>
                          ) : pending ? (
                            <span className="text-amber-600">⏳ AI parsing in background…</span>
                          ) : (
                            <span>Text extracted</span>
                          )}
                          {r.created_at && ` · ${new Date(r.created_at).toLocaleDateString()}`}
                        </p>
                      </div>
                      <button
                        onClick={() => handleDelete(r.id)}
                        disabled={deletingId === r.id}
                        title="Delete resume"
                        className="rounded-md p-1.5 text-stone-300 hover:bg-coral/10 hover:text-coral disabled:opacity-50 transition-colors"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}

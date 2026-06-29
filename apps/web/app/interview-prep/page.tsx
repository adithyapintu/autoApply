"use client";
import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { BookOpen, ChevronDown, ChevronUp, Loader2, Lightbulb, Code2, MessageSquare } from "lucide-react";
import { Sidebar } from "@/components/sidebar";
import { api } from "@/lib/api";
import type { InterviewPrep, BehavioralQuestion, TechnicalQuestion } from "@autoapply/shared";

const DIFFICULTY_STYLES = {
  easy: "bg-moss/10 text-moss",
  medium: "bg-amber-50 text-amber-700",
  hard: "bg-coral/10 text-coral",
};

function BehavioralCard({ q }: { q: BehavioralQuestion }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-lg border border-stone-200 bg-white overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-start justify-between gap-3 px-4 py-3 text-left hover:bg-stone-50"
      >
        <div>
          <p className="text-sm font-medium text-ink">{q.question}</p>
          <p className="text-xs text-stone-500 mt-0.5 capitalize">{q.theme}</p>
        </div>
        {open ? <ChevronUp className="h-4 w-4 shrink-0 text-stone-400 mt-0.5" /> : <ChevronDown className="h-4 w-4 shrink-0 text-stone-400 mt-0.5" />}
      </button>
      {open && (
        <div className="border-t border-stone-100 px-4 py-4 space-y-3">
          {q.suggested_answer ? (
            <div>
              <p className="text-xs font-medium text-stone-500 uppercase mb-1">Suggested Answer</p>
              <p className="text-sm text-stone-700 leading-relaxed">{q.suggested_answer}</p>
            </div>
          ) : (
            <p className="text-xs italic text-stone-400">
              No suggested answer — fill in based on your experience.
            </p>
          )}
          {q.star_hints.length > 0 && (
            <div>
              <p className="text-xs font-medium text-stone-500 uppercase mb-1">STAR Hints</p>
              <ul className="space-y-1">
                {q.star_hints.map((h, i) => (
                  <li key={i} className="text-xs text-stone-600">• {h}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function TechnicalCard({ q }: { q: TechnicalQuestion }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-lg border border-stone-200 bg-white overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-start justify-between gap-3 px-4 py-3 text-left hover:bg-stone-50"
      >
        <div className="flex items-start gap-2">
          <span className={`mt-0.5 shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${DIFFICULTY_STYLES[q.difficulty]}`}>
            {q.difficulty}
          </span>
          <div>
            <p className="text-sm font-medium text-ink">{q.question}</p>
            <p className="text-xs text-stone-500 mt-0.5">{q.topic}</p>
          </div>
        </div>
        {open ? <ChevronUp className="h-4 w-4 shrink-0 text-stone-400 mt-1" /> : <ChevronDown className="h-4 w-4 shrink-0 text-stone-400 mt-1" />}
      </button>
      {open && (
        <div className="border-t border-stone-100 px-4 py-3">
          <p className="text-xs text-stone-600 italic">{q.why_relevant}</p>
        </div>
      )}
    </div>
  );
}

function InterviewPrepContent() {
  const searchParams = useSearchParams();
  const initialJobId = searchParams.get("job_id") ?? "";

  const [token, setToken] = useState<string | null>(null);
  const [jobId, setJobId] = useState(initialJobId);
  const [prep, setPrep] = useState<InterviewPrep | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const t = localStorage.getItem("access_token");
    setToken(t);
    if (t && initialJobId) generate(t, initialJobId);
  }, [initialJobId]);

  async function generate(t: string, jid: string) {
    if (!jid) return;
    setLoading(true); setError(null); setPrep(null);
    try {
      const res = await api.interviewPrep(jid, t);
      setPrep(res as unknown as InterviewPrep);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Generation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-w-0 flex-1 flex-col">
      <header className="flex h-16 items-center gap-4 border-b border-stone-200 bg-white px-8">
        <BookOpen className="h-5 w-5 text-moss" />
        <h1 className="text-xl font-semibold text-ink">Interview Prep</h1>
      </header>

      <div className="max-w-3xl space-y-6 p-8">
        {/* Job ID input */}
        <div className="flex gap-3">
          <input
            value={jobId}
            onChange={(e) => setJobId(e.target.value)}
            placeholder="Paste a Job ID from the jobs page…"
            className="flex-1 rounded-md border border-stone-200 px-3 py-2 text-sm outline-none focus:border-moss"
          />
          <button
            onClick={() => token && generate(token, jobId)}
            disabled={loading || !token || !jobId}
            className="flex items-center gap-2 rounded-md bg-moss px-4 py-2 text-sm font-medium text-white hover:bg-moss/90 disabled:opacity-50"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <BookOpen className="h-4 w-4" />}
            {loading ? "Generating…" : "Generate"}
          </button>
        </div>

        {error && (
          <div className="rounded-md bg-coral/10 border border-coral/30 px-4 py-2 text-sm text-coral">{error}</div>
        )}

        {prep && (
          <>
            {/* Talking points */}
            {prep.talking_points.length > 0 && (
              <section>
                <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase text-stone-500">
                  <Lightbulb className="h-4 w-4" /> Key Talking Points
                </h2>
                <div className="rounded-lg border border-stone-200 bg-white p-4 space-y-2">
                  {prep.talking_points.map((tp, i) => (
                    <p key={i} className="flex items-start gap-2 text-sm text-stone-700">
                      <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-moss/10 text-xs font-bold text-moss">
                        {i + 1}
                      </span>
                      {tp}
                    </p>
                  ))}
                </div>
              </section>
            )}

            {/* Behavioral questions */}
            {prep.behavioral_questions.length > 0 && (
              <section>
                <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase text-stone-500">
                  <MessageSquare className="h-4 w-4" /> Behavioral Questions
                  <span className="rounded-full bg-stone-100 px-2 py-0.5 text-xs normal-case text-stone-500">
                    {prep.behavioral_questions.length}
                  </span>
                </h2>
                <div className="space-y-2">
                  {prep.behavioral_questions.map((q, i) => <BehavioralCard key={i} q={q} />)}
                </div>
              </section>
            )}

            {/* Technical questions */}
            {prep.technical_questions.length > 0 && (
              <section>
                <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase text-stone-500">
                  <Code2 className="h-4 w-4" /> Technical Questions
                  <span className="rounded-full bg-stone-100 px-2 py-0.5 text-xs normal-case text-stone-500">
                    {prep.technical_questions.length}
                  </span>
                </h2>
                <div className="space-y-2">
                  {prep.technical_questions.map((q, i) => <TechnicalCard key={i} q={q} />)}
                </div>
              </section>
            )}

            {/* Questions to ask */}
            {prep.company_questions.length > 0 && (
              <section>
                <h2 className="mb-3 text-sm font-semibold uppercase text-stone-500">Questions to Ask the Interviewer</h2>
                <div className="rounded-lg border border-stone-200 bg-white p-4 space-y-2">
                  {prep.company_questions.map((q, i) => (
                    <p key={i} className="text-sm text-stone-700">• {q}</p>
                  ))}
                </div>
              </section>
            )}

            {/* Prep tips */}
            {prep.preparation_tips.length > 0 && (
              <section className="rounded-lg border border-moss/20 bg-moss/5 p-4">
                <h2 className="mb-2 text-xs font-semibold uppercase text-moss">Preparation Tips</h2>
                {prep.preparation_tips.map((t, i) => (
                  <p key={i} className="text-sm text-moss/80">• {t}</p>
                ))}
              </section>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default function InterviewPrepPage() {
  return (
    <main className="flex min-h-screen bg-paper">
      <Sidebar />
      <Suspense fallback={<div className="flex flex-1 items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-stone-400" /></div>}>
        <InterviewPrepContent />
      </Suspense>
    </main>
  );
}

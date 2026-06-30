"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, BarChart3, TrendingUp, Zap } from "lucide-react";
import { Sidebar } from "@/components/sidebar";
import { StatGrid } from "@/components/stat-grid";
import { api } from "@/lib/api";
import type {
  AnalyticsSummary,
  FunnelData,
  MarketData,
  SourceRow,
  VelocityData,
} from "@autoapply/shared";

const EMPTY_SUMMARY: AnalyticsSummary = {
  applications_this_week: 0, applications_this_month: 0,
  interview_rate: 0, response_rate: 0, offer_rate: 0, average_match_score: 0,
};

const STAGE_LABELS: Record<string, string> = {
  draft: "Draft", applied: "Applied", phone_screen: "Phone Screen",
  interview: "Interview", offer: "Offer", rejected: "Rejected",
};
const STAGE_COLOR: Record<string, string> = {
  draft: "bg-stone-300", applied: "bg-sky-400", phone_screen: "bg-indigo-400",
  interview: "bg-amber-400", offer: "bg-moss", rejected: "bg-coral",
};

export default function AnalyticsPage() {
  const router = useRouter();
  const [summary, setSummary] = useState<AnalyticsSummary>(EMPTY_SUMMARY);
  const [funnel, setFunnel] = useState<FunnelData | null>(null);
  const [sources, setSources] = useState<SourceRow[]>([]);
  const [velocity, setVelocity] = useState<VelocityData | null>(null);
  const [market, setMarket] = useState<MarketData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const t = localStorage.getItem("access_token");
    if (!t) { router.push("/login"); return; }
    Promise.all([
      api.analytics(t).then(setSummary),
      api.analyticsFunnel(t).then(setFunnel),
      api.analyticsBySource(t).then(setSources),
      api.analyticsVelocity(t).then(setVelocity),
      api.analyticsMarket(t).then(setMarket),
    ]).catch(() => {}).finally(() => setLoading(false));
  }, [router]);

  const maxFunnelCount = funnel ? Math.max(...funnel.stages.map((s) => s.count), 1) : 1;
  const maxVelocity = velocity ? Math.max(...velocity.daily.map((d) => d.count), 1) : 1;
  const maxDemand = market ? Math.max(...market.top_skills.map((s) => s.demand), 1) : 1;

  return (
    <main className="flex min-h-screen bg-paper">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center border-b border-stone-200 bg-white px-4 md:px-8">
          <h1 className="text-lg font-semibold text-ink">Analytics</h1>
          {velocity && (
            <span className="ml-4 text-xs text-stone-500">
              {velocity.total_last_30_days} applications in the last 30 days
            </span>
          )}
        </header>

        <div className="space-y-6 p-4 md:p-8">
          {loading ? (
            <div className="text-sm text-stone-500">Loading…</div>
          ) : (
            <>
              {/* Velocity warnings */}
              {velocity?.warnings && velocity.warnings.length > 0 && (
                <div className="space-y-2">
                  {velocity.warnings.map((w) => (
                    <div key={w} className="flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800">
                      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                      {w}
                    </div>
                  ))}
                </div>
              )}

              {/* Summary stats */}
              <StatGrid summary={summary} />

              <div className="grid gap-6 lg:grid-cols-2">
                {/* Application Funnel */}
                <section className="rounded-md border border-stone-200 bg-white p-5">
                  <div className="mb-4 flex items-center gap-2">
                    <BarChart3 className="h-4 w-4 text-steel" />
                    <h2 className="text-sm font-semibold text-ink">Application Funnel</h2>
                    {funnel?.median_days_to_response != null && (
                      <span className="ml-auto text-xs text-stone-500">
                        Median response: {funnel.median_days_to_response}d
                      </span>
                    )}
                  </div>
                  <div className="space-y-2.5">
                    {funnel?.stages.map(({ stage, count }) => (
                      <div key={stage} className="flex items-center gap-3">
                        <span className="w-24 shrink-0 text-xs text-stone-500">{STAGE_LABELS[stage] ?? stage}</span>
                        <div className="flex-1 rounded-full bg-stone-100">
                          <div
                            className={`h-2.5 rounded-full transition-all ${STAGE_COLOR[stage] ?? "bg-stone-400"}`}
                            style={{ width: `${Math.max(2, (count / maxFunnelCount) * 100)}%` }}
                          />
                        </div>
                        <span className="w-6 text-right text-xs font-semibold text-ink">{count}</span>
                      </div>
                    ))}
                  </div>
                  {funnel && funnel.match_score_correlation.high_score_count > 0 && (
                    <div className="mt-4 border-t border-stone-100 pt-4 text-xs text-stone-500 space-y-1">
                      <div>High match (≥70) response rate: <strong className="text-moss">{funnel.match_score_correlation.high_score_response_rate}%</strong></div>
                      <div>Low match (&lt;70) response rate: <strong className="text-coral">{funnel.match_score_correlation.low_score_response_rate}%</strong></div>
                    </div>
                  )}
                </section>

                {/* Application Velocity */}
                <section className="rounded-md border border-stone-200 bg-white p-5">
                  <div className="mb-4 flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-steel" />
                    <h2 className="text-sm font-semibold text-ink">Application Velocity</h2>
                    {velocity && (
                      <span className="ml-auto text-xs text-stone-500">
                        7-day avg: <strong className="text-ink">{velocity.rolling_7day_avg}</strong>/day
                      </span>
                    )}
                  </div>
                  {velocity && (
                    <>
                      <div className="flex h-20 items-end gap-0.5">
                        {velocity.daily.map(({ date, count }) => (
                          <div
                            key={date}
                            title={`${date}: ${count}`}
                            className="flex-1 rounded-t bg-moss/70 transition-all hover:bg-moss"
                            style={{ height: `${Math.max(4, (count / maxVelocity) * 100)}%` }}
                          />
                        ))}
                      </div>
                      <div className="mt-1 flex justify-between text-xs text-stone-400">
                        <span>{velocity.daily[0]?.date.slice(5)}</span>
                        <span>{velocity.daily[velocity.daily.length - 1]?.date.slice(5)}</span>
                      </div>
                      <p className="mt-3 text-xs text-stone-500">
                        Suggested monthly target: <strong className="text-ink">{velocity.suggested_monthly_target}</strong> applications
                      </p>
                    </>
                  )}
                </section>
              </div>

              <div className="grid gap-6 lg:grid-cols-2">
                {/* By Source */}
                <section className="rounded-md border border-stone-200 bg-white">
                  <div className="flex items-center gap-2 border-b border-stone-200 px-5 py-3">
                    <Zap className="h-4 w-4 text-steel" />
                    <h2 className="text-sm font-semibold text-ink">Effectiveness by Source</h2>
                  </div>
                  {sources.length === 0 ? (
                    <p className="px-5 py-6 text-sm text-stone-400">No application data yet.</p>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[420px] text-left text-xs">
                        <thead className="bg-stone-50 text-stone-500 uppercase">
                          <tr>
                            <th className="px-4 py-2">Source</th>
                            <th className="px-4 py-2 text-right">Apps</th>
                            <th className="px-4 py-2 text-right">Response</th>
                            <th className="px-4 py-2 text-right">Interview</th>
                            <th className="px-4 py-2 text-right">Avg Score</th>
                          </tr>
                        </thead>
                        <tbody>
                          {sources.map((row) => (
                            <tr key={row.source} className="border-t border-stone-100">
                              <td className="px-4 py-2 font-medium capitalize text-ink">{row.source}</td>
                              <td className="px-4 py-2 text-right text-stone-600">{row.total}</td>
                              <td className="px-4 py-2 text-right text-stone-600">{row.response_rate}%</td>
                              <td className="px-4 py-2 text-right text-stone-600">{row.interview_rate}%</td>
                              <td className="px-4 py-2 text-right text-stone-600">{row.avg_match_score ?? "—"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </section>

                {/* Market Skill Demand */}
                <section className="rounded-md border border-stone-200 bg-white p-5">
                  <div className="mb-1 flex items-center gap-2">
                    <h2 className="text-sm font-semibold text-ink">Market Skill Demand</h2>
                    {market && (
                      <span className="ml-auto text-xs text-stone-400">{market.total_jobs_analyzed} jobs analysed</span>
                    )}
                  </div>
                  {!market || market.top_skills.length === 0 ? (
                    <p className="mt-4 text-sm text-stone-400">Discover jobs first to see market trends.</p>
                  ) : (
                    <div className="mt-3 space-y-2">
                      {market.top_skills.slice(0, 12).map(({ skill, demand, in_profile }) => (
                        <div key={skill} className="flex items-center gap-3">
                          <span className={`w-28 shrink-0 text-xs ${in_profile ? "font-medium text-moss" : "text-stone-500"}`}>
                            {skill}{in_profile && " ✓"}
                          </span>
                          <div className="flex-1 rounded-full bg-stone-100">
                            <div
                              className={`h-2 rounded-full ${in_profile ? "bg-moss" : "bg-stone-300"}`}
                              style={{ width: `${(demand / maxDemand) * 100}%` }}
                            />
                          </div>
                          <span className="w-8 text-right text-xs text-stone-400">{demand}</span>
                        </div>
                      ))}
                      <p className="pt-1 text-xs text-stone-400">
                        Green = in your profile · {market.profile_skill_count} skills tracked
                      </p>
                    </div>
                  )}
                </section>
              </div>
            </>
          )}
        </div>
      </div>
    </main>
  );
}

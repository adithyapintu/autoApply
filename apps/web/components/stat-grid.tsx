import type { AnalyticsSummary } from "@autoapply/shared";

const formatter = new Intl.NumberFormat("en", { maximumFractionDigits: 1 });

export function StatGrid({ summary }: { summary: AnalyticsSummary }) {
  const stats = [
    ["This week", summary.applications_this_week],
    ["This month", summary.applications_this_month],
    ["Interview rate", `${formatter.format(summary.interview_rate)}%`],
    ["Response rate", `${formatter.format(summary.response_rate)}%`],
    ["Offer rate", `${formatter.format(summary.offer_rate)}%`],
    ["Avg match", formatter.format(summary.average_match_score)]
  ];

  return (
    <section className="grid grid-cols-2 gap-3 lg:grid-cols-6">
      {stats.map(([label, value]) => (
        <div key={label} className="rounded-md border border-stone-200 bg-white p-4">
          <div className="text-xs uppercase text-stone-500">{label}</div>
          <div className="mt-2 text-2xl font-semibold text-ink">{value}</div>
        </div>
      ))}
    </section>
  );
}


import { BarChart3, BriefcaseBusiness, FileText, Gauge, Settings, UserRound } from "lucide-react";

const items = [
  { label: "Dashboard", icon: Gauge },
  { label: "Jobs", icon: BriefcaseBusiness },
  { label: "Applications", icon: FileText },
  { label: "Profile", icon: UserRound },
  { label: "Analytics", icon: BarChart3 },
  { label: "Settings", icon: Settings }
];

export function Sidebar() {
  return (
    <aside className="hidden w-60 shrink-0 border-r border-stone-200 bg-white px-4 py-5 md:block">
      <div className="mb-8 text-lg font-semibold text-ink">AutoApply AI</div>
      <nav className="space-y-1">
        {items.map((item) => (
          <button
            key={item.label}
            className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm text-stone-700 hover:bg-stone-100"
            title={item.label}
          >
            <item.icon className="h-4 w-4 text-steel" aria-hidden="true" />
            {item.label}
          </button>
        ))}
      </nav>
    </aside>
  );
}


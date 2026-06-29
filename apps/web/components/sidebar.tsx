"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, Bell, BookOpen, BriefcaseBusiness, FileText, Gauge, Settings, ShieldCheck, UserRound } from "lucide-react";

const items = [
  { label: "Dashboard", icon: Gauge, href: "/" },
  { label: "Jobs", icon: BriefcaseBusiness, href: "/jobs" },
  { label: "Applications", icon: FileText, href: "/applications" },
  { label: "Automation", icon: ShieldCheck, href: "/automation" },
  { label: "Saved Searches", icon: Bell, href: "/saved-searches" },
  { label: "Interview Prep", icon: BookOpen, href: "/interview-prep" },
  { label: "Resumes", icon: FileText, href: "/resumes" },
  { label: "Profile", icon: UserRound, href: "/profile" },
  { label: "Analytics", icon: BarChart3, href: "/analytics" },
  { label: "Settings", icon: Settings, href: "/settings" },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden w-60 shrink-0 border-r border-stone-200 bg-white px-4 py-5 md:block">
      <Link href="/" className="mb-8 block text-lg font-semibold text-ink hover:text-moss">
        AutoApply AI
      </Link>
      <nav className="space-y-1">
        {items.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.label}
              href={item.href}
              className={`flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm transition-colors ${
                active
                  ? "bg-moss/10 font-medium text-moss"
                  : "text-stone-700 hover:bg-stone-100"
              }`}
            >
              <item.icon className={`h-4 w-4 ${active ? "text-moss" : "text-steel"}`} aria-hidden="true" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}


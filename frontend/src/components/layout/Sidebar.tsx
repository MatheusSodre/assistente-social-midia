import {
  Calendar,
  History,
  LayoutDashboard,
  LayoutTemplate,
  Sparkles,
  Wand2,
} from "lucide-react";
import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";

const items = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/criar", label: "Criar Post", icon: Wand2 },
  { to: "/brand-memory", label: "Brand Memory", icon: Sparkles },
  { to: "/historico", label: "Histórico", icon: History },
  { to: "/templates", label: "Templates", icon: LayoutTemplate },
];

export function Sidebar() {
  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-border bg-card">
      <div className="flex h-14 items-center gap-2 border-b border-border px-6">
        <Calendar className="h-5 w-5 text-primary" />
        <span className="font-semibold">Orbitaia</span>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {items.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-accent/10 hover:text-foreground",
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-border px-6 py-3 text-xs text-muted-foreground">
        v0.1.0 · MVP
      </div>
    </aside>
  );
}

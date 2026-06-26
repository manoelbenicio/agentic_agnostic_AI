"use client";

import {
  Activity,
  Blocks,
  CircleDollarSign,
  Gauge,
  LayoutDashboard,
  Network,
  Radio,
} from "lucide-react";
import type { ReactNode } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";

import { ThemeToggle } from "@/components/theme-toggle";
import { HealthBadge } from "@/components/dashboard/HealthBadge";

const navItems = [
  { label: "Dashboard", icon: LayoutDashboard, href: "/" },
  { label: "Squad Builder", icon: Network, href: "/squad-builder" },
  { label: "Live Panel", icon: Radio, href: "/live" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="grid min-h-screen lg:grid-cols-[264px_minmax(0,1fr)]">
        <aside className="hidden border-r border-border bg-sidebar text-sidebar-foreground lg:block">
          <div className="flex h-16 items-center gap-3 border-b border-sidebar-border px-5">
            <div className="flex size-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <Gauge className="size-5" />
            </div>
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold">AOP Control</div>
              <div className="truncate text-xs text-muted-foreground">
                Local-first runtime
              </div>
            </div>
          </div>
          <nav className="space-y-1 p-3">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.label}
                  href={item.href}
                  className={
                    isActive
                      ? "flex h-9 items-center gap-3 rounded-md bg-sidebar-accent px-3 text-sm font-medium text-sidebar-accent-foreground"
                      : "flex h-9 items-center gap-3 rounded-md px-3 text-sm text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                  }
                >
                  <Icon className="size-4" />
                  <span>{item.label}</span>
                  {item.label === "Live Panel" && (
                    <span className="ml-auto size-2 animate-pulse rounded-full bg-success" />
                  )}
                </Link>
              );
            })}
          </nav>
        </aside>
        <div className="min-w-0">
          <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-border bg-background/90 px-4 backdrop-blur md:px-6">
            <div className="min-w-0">
              <div className="text-sm font-semibold">
                Agnostic Orchestration Platform
              </div>
              <div className="text-xs text-muted-foreground">
                HerdMaster + Herdr runtime foundation
              </div>
            </div>
            <div className="flex items-center gap-3">
              <HealthBadge />
              <ThemeToggle />
            </div>
          </header>
          <main className="mx-auto w-full max-w-7xl px-4 py-6 md:px-6">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}

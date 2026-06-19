"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  MessageSquare,
  Sparkles,
  UserCog,
  Users,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { useAuth } from "@/features/auth";

const navItems = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Customers", href: "/customers", icon: Users },
  { label: "Interactions", href: "/interactions", icon: MessageSquare },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();

  const isActive = (href: string) =>
    pathname === href || pathname.startsWith(`${href}/`);

  const linkClass = (href: string) =>
    cn(
      "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
      isActive(href)
        ? "bg-primary text-primary-foreground shadow-md shadow-primary/25"
        : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
    );

  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-border/60 bg-sidebar md:flex">
      <div className="flex h-16 items-center gap-2 border-b border-border/60 px-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary shadow-md shadow-primary/30">
          <Sparkles className="h-5 w-5 text-primary-foreground" />
        </div>
        <div>
          <span className="text-sm font-bold tracking-tight text-sidebar-foreground">
            CSP
          </span>
          <p className="text-[10px] text-muted-foreground leading-none">
            Customer Success
          </p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 p-4">
        {navItems.map(({ label, href, icon: Icon }) => (
          <Link key={href} href={href} className={linkClass(href)}>
            <Icon className="h-4 w-4 shrink-0" />
            {label}
          </Link>
        ))}

        {user?.role === "ADMIN" && (
          <div className="mt-4">
            <p className="mb-1 px-3 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Admin
            </p>
            <Link href="/admin/users" className={linkClass("/admin/users")}>
              <UserCog className="h-4 w-4 shrink-0" />
              Users
            </Link>
          </div>
        )}
      </nav>

      <div className="border-t border-border/60 p-4">
        <div className="rounded-lg bg-accent/50 px-3 py-2.5">
          <p className="text-xs font-medium text-accent-foreground">
            AI-Powered Insights
          </p>
          <p className="mt-0.5 text-[10px] text-muted-foreground">
            Analyze interactions with Gemini
          </p>
        </div>
      </div>
    </aside>
  );
}

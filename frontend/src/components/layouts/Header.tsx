"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, LogOut, MessageSquare, Users } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/features/auth";
import { useToast } from "@/components/ui/use-toast";
import { cn } from "@/lib/utils";

const mobileNav = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Customers", href: "/customers", icon: Users },
  { label: "Interactions", href: "/interactions", icon: MessageSquare },
];

const roleVariant: Record<string, "default" | "secondary" | "destructive"> = {
  ADMIN: "destructive",
  MANAGER: "default",
  VIEWER: "secondary",
};

export function Header() {
  const pathname = usePathname();
  const { toast } = useToast();
  const { user, logout, isLoading } = useAuth();

  async function handleLogout() {
    try {
      await logout();
    } catch {
      toast({
        variant: "destructive",
        title: "Logout failed",
        description: "Please try again.",
      });
    }
  }

  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-card/80 backdrop-blur-md">
      <div className="flex h-16 items-center justify-between px-4 sm:px-6">
        <nav className="flex items-center gap-1 md:hidden">
          {mobileNav.map(({ label, href, icon: Icon }) => {
            const active =
              pathname === href || pathname.startsWith(`${href}/`);
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors",
                  active
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                <Icon className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">{label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="hidden md:block" />

        <div className="flex items-center gap-2">
          {user && (
            <>
              <span className="hidden text-sm text-muted-foreground sm:block">
                {user.first_name} {user.last_name}
              </span>
              <Badge variant={roleVariant[user.role] ?? "secondary"}>
                {user.role}
              </Badge>
            </>
          )}

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="h-9 gap-2 border-primary/20"
              >
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/15 text-xs font-semibold text-primary">
                  {user?.first_name?.[0] ?? "?"}
                </span>
                <span className="hidden sm:inline">Account</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-52">
              <DropdownMenuLabel>
                <p className="font-medium">
                  {user?.first_name} {user?.last_name}
                </p>
                <p className="text-xs font-normal text-muted-foreground">
                  {user?.email}
                </p>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-destructive focus:text-destructive"
                disabled={isLoading}
                onClick={handleLogout}
              >
                <LogOut className="mr-2 h-4 w-4" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}

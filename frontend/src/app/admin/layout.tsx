import type { ReactNode } from "react";
import type { Metadata } from "next";

import { AppShell } from "@/components/layouts/AppShell";

export const metadata: Metadata = {
  title: "Admin",
  description: "Platform administration — manage users, roles, and settings.",
  robots: { index: false, follow: false },
};

export default function AdminLayout({ children }: { children: ReactNode }) {
  return <AppShell>{children}</AppShell>;
}

import type { ReactNode } from "react";
import type { Metadata } from "next";

import { AppShell } from "@/components/layouts/AppShell";

export const metadata: Metadata = {
  title: "Dashboard",
  description:
    "Executive overview of customer health metrics, interaction trends, sentiment analytics, and AI-powered risk detection.",
  robots: { index: false, follow: false },
};

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return <AppShell>{children}</AppShell>;
}

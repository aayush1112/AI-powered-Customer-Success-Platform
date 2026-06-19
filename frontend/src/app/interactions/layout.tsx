import type { ReactNode } from "react";
import type { Metadata } from "next";

import { AppShell } from "@/components/layouts/AppShell";

export const metadata: Metadata = {
  title: "Interactions",
  description:
    "Log and review all customer interactions — meetings, calls, emails, and QBRs. Generate AI-powered insights from meeting notes.",
  robots: { index: false, follow: false },
};

export default function InteractionsLayout({
  children,
}: {
  children: ReactNode;
}) {
  return <AppShell>{children}</AppShell>;
}

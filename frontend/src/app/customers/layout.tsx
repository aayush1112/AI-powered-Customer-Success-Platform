import type { ReactNode } from "react";
import type { Metadata } from "next";

import { AppShell } from "@/components/layouts/AppShell";

export const metadata: Metadata = {
  title: "Customers",
  description:
    "View and manage all customer accounts. Filter by status, search by name, and track health scores across your entire portfolio.",
  robots: { index: false, follow: false },
};

export default function CustomersLayout({ children }: { children: ReactNode }) {
  return <AppShell>{children}</AppShell>;
}

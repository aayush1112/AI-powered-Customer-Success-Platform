import type { ReactNode } from "react";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Create Account",
  description:
    "Create your Customer Success Platform account and start managing customer relationships, tracking interactions, and unlocking AI insights.",
  alternates: {
    canonical: "/register",
  },
};

export default function RegisterLayout({ children }: { children: ReactNode }) {
  return <>{children}</>;
}

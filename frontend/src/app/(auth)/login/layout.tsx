import type { ReactNode } from "react";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sign In",
  description:
    "Sign in to the Customer Success Platform to manage customer accounts, track interactions, and access AI-powered insights.",
  alternates: {
    canonical: "/login",
  },
};

export default function LoginLayout({ children }: { children: ReactNode }) {
  return <>{children}</>;
}

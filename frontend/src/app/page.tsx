import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export const metadata: Metadata = {
  title: "AI-Powered Customer Success Platform",
  description:
    "Manage customer relationships, track every interaction, and unlock AI-powered insights with Gemini analytics. Get started for free.",
  alternates: {
    canonical: "/",
  },
  openGraph: {
    title: "AI-Powered Customer Success Platform",
    description:
      "Manage customer relationships, track every interaction, and unlock AI-powered insights with Gemini analytics.",
    url: "/",
  },
};

export default function HomePage() {
  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center page-gradient p-8">
      <div className="absolute inset-0 auth-gradient opacity-[0.03]" />
      <Card className="relative w-full max-w-lg border-0 shadow-glow glass-card">
        <CardHeader className="space-y-3 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary shadow-lg shadow-primary/30">
            <Sparkles className="h-7 w-7 text-primary-foreground" />
          </div>
          <div className="flex flex-col items-center gap-2">
            <CardTitle className="text-3xl font-bold tracking-tight">
              <span className="text-gradient">Customer Success</span> Platform
            </CardTitle>
            <Badge variant="default">AI-Powered</Badge>
          </div>
          <CardDescription className="text-base">
            Manage relationships, track interactions, and unlock insights with
            Gemini-powered analytics.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:justify-center">
            <Button asChild size="lg">
              <Link href="/login">
                Sign in
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link href="/register">Create account</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}

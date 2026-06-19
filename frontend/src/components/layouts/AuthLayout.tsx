import { type ReactNode } from "react";

interface AuthLayoutProps {
  children: ReactNode;
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/50">
      <div className="w-full max-w-md space-y-8 px-4">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight">Customer Success Platform</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            AI-Powered Customer Success Management
          </p>
        </div>
        {children}
      </div>
    </div>
  );
}

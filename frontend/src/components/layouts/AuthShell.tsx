import type { ReactNode } from "react";

interface AuthShellProps {
  children: ReactNode;
  title: string;
  subtitle: string;
}

export function AuthBrandingPanel({ title, subtitle }: Omit<AuthShellProps, "children">) {
  return (
    <div className="relative hidden flex-1 flex-col justify-between overflow-hidden auth-gradient p-10 text-white lg:flex">
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggIGQ9Ik0zNiAxOGMzLjMxNCAwIDYgMi42ODYgNiA2cy0yLjY4NiA2LTYgNi02LTIuNjg2LTYtNiAyLjY4Ni02IDYtNnoiLz48L2c+PC9nPjwvc3ZnPg==')] opacity-40" />
      <div className="relative z-10">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/20 backdrop-blur-sm">
            <span className="text-lg font-bold">CSP</span>
          </div>
          <div>
            <p className="text-lg font-bold">Customer Success Platform</p>
            <p className="text-sm text-white/80">AI-powered relationship management</p>
          </div>
        </div>
      </div>

      <div className="relative z-10 space-y-6">
        <h2 className="text-3xl font-bold leading-tight tracking-tight">
          {title}
        </h2>
        <p className="max-w-md text-lg text-white/85">{subtitle}</p>
        <ul className="space-y-3 text-sm text-white/75">
          <li className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-white" />
            Track customer health and engagement
          </li>
          <li className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-white" />
            Log meetings, calls, and QBRs
          </li>
          <li className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-white" />
            Generate AI insights from interactions
          </li>
        </ul>
      </div>

      <p className="relative z-10 text-xs text-white/60">
        &copy; {new Date().getFullYear()} Customer Success Platform
      </p>
    </div>
  );
}

export function AuthFormPanel({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center p-6 sm:p-10">
      <div className="w-full max-w-md">{children}</div>
    </div>
  );
}

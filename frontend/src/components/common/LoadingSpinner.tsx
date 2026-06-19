import { cn } from "@/lib/utils";

const sizes = { sm: "h-4 w-4", md: "h-8 w-8", lg: "h-12 w-12" } as const;

interface LoadingSpinnerProps {
  className?: string;
  size?: keyof typeof sizes;
}

export function LoadingSpinner({ className, size = "md" }: LoadingSpinnerProps) {
  return (
    <div
      role="status"
      aria-label="Loading"
      className={cn(
        "animate-spin rounded-full border-2 border-muted border-t-primary",
        sizes[size],
        className
      )}
    />
  );
}

export function LoadingPage() {
  return (
    <div className="flex h-full min-h-[200px] items-center justify-center">
      <LoadingSpinner size="lg" />
    </div>
  );
}

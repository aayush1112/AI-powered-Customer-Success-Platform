import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

type Accent = "primary" | "success" | "warning" | "destructive";

const accentStyles: Record<Accent, { card: string; icon: string; value: string }> = {
  primary: {
    card: "border-primary/20 bg-gradient-to-br from-primary/5 to-transparent",
    icon: "bg-primary/15 text-primary",
    value: "text-primary",
  },
  success: {
    card: "border-success/20 bg-gradient-to-br from-success/5 to-transparent",
    icon: "bg-success/15 text-success",
    value: "text-success",
  },
  warning: {
    card: "border-warning/20 bg-gradient-to-br from-warning/5 to-transparent",
    icon: "bg-warning/15 text-warning",
    value: "text-warning",
  },
  destructive: {
    card: "border-destructive/20 bg-gradient-to-br from-destructive/5 to-transparent",
    icon: "bg-destructive/15 text-destructive",
    value: "text-destructive",
  },
};

interface MetricCardProps {
  title: string;
  value: number;
  description?: string;
  icon?: React.ReactNode;
  accent?: Accent;
  valueClassName?: string;
}

export function MetricCard({
  title,
  value,
  description,
  icon,
  accent = "primary",
  valueClassName,
}: MetricCardProps) {
  const styles = accentStyles[accent];

  return (
    <Card className={cn("overflow-hidden", styles.card)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        {icon && (
          <div
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-lg",
              styles.icon
            )}
          >
            {icon}
          </div>
        )}
      </CardHeader>
      <CardContent>
        <div
          className={cn(
            "text-3xl font-bold tracking-tight",
            valueClassName ?? styles.value
          )}
        >
          {value.toLocaleString()}
        </div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1.5">{description}</p>
        )}
      </CardContent>
    </Card>
  );
}

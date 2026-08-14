import { CheckCircle2, CircleDashed, Loader2, XCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { ResearchStatus } from "@/types/research";

const STATUS_CONFIG: Record<
  ResearchStatus,
  { label: string; icon: typeof CheckCircle2; className: string }
> = {
  pending: {
    label: "Pending",
    icon: CircleDashed,
    className: "bg-muted text-muted-foreground",
  },
  running: {
    label: "Running",
    icon: Loader2,
    className: "bg-primary/10 text-primary",
  },
  completed: {
    label: "Completed",
    icon: CheckCircle2,
    className: "bg-success/15 text-success",
  },
  failed: {
    label: "Failed",
    icon: XCircle,
    className: "bg-destructive/10 text-destructive",
  },
};

export function ResearchStatusBadge({ status }: { status: ResearchStatus }) {
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;

  return (
    <Badge variant="outline" className={cn("border-transparent font-medium", config.className)}>
      <Icon className={cn("size-3", status === "running" && "animate-spin")} />
      {config.label}
    </Badge>
  );
}

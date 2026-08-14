"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Check, Loader2 } from "lucide-react";

import { RESEARCH_STAGES, stageLabel } from "@/lib/research-stages";
import { cn } from "@/lib/utils";

export function StageProgress({ currentStep, iteration }: { currentStep: string | null; iteration: number }) {
  const [seen, setSeen] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (currentStep) {
      setSeen((prev) => (prev.has(currentStep) ? prev : new Set(prev).add(currentStep)));
    }
  }, [currentStep]);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Loader2 className="size-4 animate-spin text-primary" />
        <p className="text-sm font-medium">{stageLabel(currentStep)}</p>
        {iteration > 0 && (
          <span className="rounded-full bg-muted px-2 py-0.5 text-[11px] text-muted-foreground">
            Reflection pass {iteration}
          </span>
        )}
      </div>

      <ol className="space-y-1.5">
        {RESEARCH_STAGES.map((stage) => {
          const isCurrent = stage.key === currentStep;
          const isDone = seen.has(stage.key) && !isCurrent;
          return (
            <li key={stage.key} className="flex items-center gap-2.5 text-sm">
              <span
                className={cn(
                  "flex size-5 shrink-0 items-center justify-center rounded-full border text-[10px] transition-colors",
                  isDone && "border-success/40 bg-success/15 text-success",
                  isCurrent && "border-primary/50 bg-primary/10 text-primary",
                  !isDone && !isCurrent && "border-border text-transparent"
                )}
              >
                {isDone ? (
                  <Check className="size-3" />
                ) : isCurrent ? (
                  <motion.span
                    animate={{ scale: [1, 1.3, 1] }}
                    transition={{ duration: 1.2, repeat: Infinity }}
                    className="size-1.5 rounded-full bg-primary"
                  />
                ) : (
                  <span className="size-1.5 rounded-full bg-border" />
                )}
              </span>
              <span
                className={cn(
                  "transition-colors",
                  isCurrent && "font-medium text-foreground",
                  isDone && "text-muted-foreground",
                  !isDone && !isCurrent && "text-muted-foreground/50"
                )}
              >
                {stage.label}
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Bot, Flag, TriangleAlert } from "lucide-react";

import { ROBOT_MILESTONES, stageIndex, stageStatusText } from "@/lib/research-stages";
import { cn } from "@/lib/utils";
import type { ResearchStatus } from "@/types/research";

const MILESTONE_INDICES = ROBOT_MILESTONES.map((m) => stageIndex(m.key));
const MILESTONE_POSITIONS = ROBOT_MILESTONES.map((_, i) => (i / (ROBOT_MILESTONES.length - 1)) * 100);

function robotPositionFor(effectiveIndex: number): number {
  if (effectiveIndex <= MILESTONE_INDICES[0]) return MILESTONE_POSITIONS[0];

  for (let i = 0; i < MILESTONE_INDICES.length - 1; i++) {
    const from = MILESTONE_INDICES[i];
    const to = MILESTONE_INDICES[i + 1];
    if (effectiveIndex <= to) {
      const t = Math.max(0, Math.min(1, (effectiveIndex - from) / (to - from)));
      return MILESTONE_POSITIONS[i] + (MILESTONE_POSITIONS[i + 1] - MILESTONE_POSITIONS[i]) * t;
    }
  }
  return MILESTONE_POSITIONS[MILESTONE_POSITIONS.length - 1];
}

interface RobotProgressProps {
  currentStep: string | null;
  iteration: number;
  status: ResearchStatus;
  query: string;
}

export function RobotProgress({ currentStep, iteration, status, query }: RobotProgressProps) {
  // Tracks the furthest stage genuinely reached, monotonically — the reflection
  // loop can send `currentStep` back to an earlier node on iteration 2+, and the
  // robot must never appear to walk backwards for progress that already happened.
  const [maxIndexSeen, setMaxIndexSeen] = useState(-1);

  useEffect(() => {
    const idx = stageIndex(currentStep);
    if (idx > maxIndexSeen) setMaxIndexSeen(idx);
  }, [currentStep, maxIndexSeen]);

  const failed = status === "failed";
  const completed = status === "completed";
  const effectiveIndex = completed ? MILESTONE_INDICES[MILESTONE_INDICES.length - 1] : maxIndexSeen;
  const robotX = completed ? 100 : robotPositionFor(effectiveIndex);
  const isActive = !completed && !failed;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <p className="text-sm font-medium text-foreground">
          {failed ? "Research stalled" : completed ? "Research complete" : stageStatusText(currentStep, query)}
        </p>
        {iteration > 0 && (
          <span className="rounded-full bg-muted px-2 py-0.5 text-[11px] text-muted-foreground">
            Reflection pass {iteration}
          </span>
        )}
      </div>

      <div className="relative h-48 overflow-hidden rounded-2xl border bg-gradient-to-b from-muted/50 to-muted/10 px-7 pt-6 pb-12 sm:h-60 sm:px-10 sm:pt-8 sm:pb-14">
        <div className="absolute inset-x-7 top-[74px] h-2.5 rounded-full bg-border sm:inset-x-10 sm:top-[100px] sm:h-3">
          <motion.div
            className={cn("h-full rounded-full", failed ? "bg-destructive/60" : "bg-primary/60")}
            initial={false}
            animate={{ width: `${robotX}%` }}
            transition={{ type: "spring", stiffness: 70, damping: 18 }}
          />
        </div>

        <motion.div
          className="absolute top-[58px] z-10 flex -translate-x-1/2 flex-col items-center gap-1.5 sm:top-[80px]"
          initial={false}
          animate={{ left: `${robotX}%` }}
          transition={{ type: "spring", stiffness: 70, damping: 18 }}
        >
          {isActive && (
            <motion.span
              aria-hidden
              className="absolute top-1 size-10 rounded-full bg-primary/25 sm:size-12"
              animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0, 0.5] }}
              transition={{ duration: 1.4, repeat: Infinity, ease: "easeInOut" }}
            />
          )}
          <motion.span
            className={cn(
              "relative flex size-10 items-center justify-center rounded-full text-primary-foreground shadow-md ring-4 ring-background sm:size-12",
              failed ? "bg-destructive" : completed ? "bg-success" : "bg-primary"
            )}
            animate={isActive ? { y: [0, -5, 0] } : { y: 0 }}
            transition={isActive ? { duration: 0.55, repeat: Infinity, ease: "easeInOut" } : undefined}
          >
            {failed ? (
              <TriangleAlert className="size-5 sm:size-6" />
            ) : completed ? (
              <Flag className="size-5 sm:size-6" />
            ) : (
              <Bot className="size-5 sm:size-6" />
            )}
          </motion.span>
        </motion.div>

        <div className="absolute inset-x-7 bottom-4 flex justify-between gap-2 sm:inset-x-10 sm:bottom-5 sm:gap-4">
          {ROBOT_MILESTONES.map((milestone, i) => {
            const milestoneIndex = MILESTONE_INDICES[i];
            const isDone = completed || milestoneIndex < maxIndexSeen;
            const isCurrent = !completed && !failed && milestoneIndex === maxIndexSeen;
            const Icon = milestone.icon;

            return (
              <div
                key={milestone.key}
                className="flex min-w-0 flex-1 flex-col items-center gap-1.5 px-0.5 text-center first:items-start first:text-left last:items-end last:text-right"
              >
                <span
                  className={cn(
                    "flex size-8 shrink-0 items-center justify-center rounded-full border text-xs transition-colors sm:size-9",
                    isDone && "border-success/40 bg-success/15 text-success",
                    isCurrent && "border-primary/50 bg-primary/10 text-primary",
                    !isDone && !isCurrent && "border-border bg-background text-muted-foreground/50"
                  )}
                >
                  <Icon className="size-3.5 sm:size-4" />
                </span>
                <span
                  className={cn(
                    "hidden text-xs leading-tight text-balance sm:block",
                    isCurrent && "font-medium text-foreground",
                    isDone && "text-muted-foreground",
                    !isDone && !isCurrent && "text-muted-foreground/40"
                  )}
                >
                  {milestone.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

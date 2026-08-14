"use client";

import { use } from "react";
import Link from "next/link";
import { AlertTriangle, ArrowLeft, Gauge, Lock, RotateCw } from "lucide-react";
import { motion } from "framer-motion";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { SiteHeader } from "@/components/layout/site-header";
import { AssistantMessage, UserMessage } from "@/components/research/message-bubble";
import { RobotProgress } from "@/components/research/robot-progress";
import { ReportView } from "@/components/research/report-view";

import { useResearchRun } from "@/hooks/use-research";

export default function ResearchDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: run, isLoading, isError } = useResearchRun(id);
  const active = run?.status === "pending" || run?.status === "running";

  return (
    <>
      <SiteHeader title="Research" />

      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col">
        <div className="flex-1 space-y-6 p-4 pb-8 md:p-6">
          <Button variant="ghost" size="sm" className="w-fit" nativeButton={false} render={<Link href="/research" />}>
            <ArrowLeft />
            Back to history
          </Button>

          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-6 w-2/3 self-end" />
              <Skeleton className="h-32 w-full" />
            </div>
          ) : isError || !run ? (
            <div className="flex flex-col items-center gap-2 rounded-xl border py-16 text-center">
              <AlertTriangle className="size-8 text-destructive" />
              <p className="text-sm font-medium">Couldn&apos;t load this research run</p>
              <p className="text-sm text-muted-foreground">It may not exist, or you may not have access to it.</p>
            </div>
          ) : (
            <>
              <UserMessage query={run.query} />

              <AssistantMessage>
                {active && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="rounded-2xl rounded-tl-md border bg-card px-4 py-4"
                  >
                    <RobotProgress
                      currentStep={run.current_step}
                      iteration={run.iteration}
                      status={run.status}
                      query={run.query}
                    />
                  </motion.div>
                )}

                {run.status === "failed" && (
                  <div className="space-y-3 rounded-2xl rounded-tl-md border border-destructive/30 bg-destructive/5 px-4 py-4">
                    <p className="text-sm font-medium text-destructive">This research run failed</p>
                    {run.error && <p className="text-sm text-muted-foreground">{run.error}</p>}
                    <Button variant="outline" size="sm" nativeButton={false} render={<Link href="/research/new" />}>
                      <RotateCw />
                      Try again
                    </Button>
                  </div>
                )}

                {run.status === "completed" && run.report && (
                  <div className="space-y-3">
                    <div className="flex flex-wrap items-center gap-2">
                      {run.quality_score != null && (
                        <Tooltip>
                          <TooltipTrigger
                            render={
                              <Badge variant="outline" className="gap-1">
                                <Gauge className="size-3" />
                                Quality {run.quality_score.toFixed(0)}
                              </Badge>
                            }
                          />
                          <TooltipContent>
                            Confidence score from DeepLens&apos;s verification and reflection passes
                          </TooltipContent>
                        </Tooltip>
                      )}
                      {run.iteration > 0 && <Badge variant="outline">{run.iteration} reflection pass{run.iteration > 1 ? "es" : ""}</Badge>}
                      {run.completed_at && (
                        <span className="text-xs text-muted-foreground">
                          Completed {new Date(run.completed_at).toLocaleString()}
                        </span>
                      )}
                    </div>

                    <div className="rounded-2xl rounded-tl-md border bg-card px-4 py-4 sm:px-6 sm:py-5">
                      <ReportView report={run.report} query={run.query} runId={run.id} />
                    </div>
                  </div>
                )}
              </AssistantMessage>
            </>
          )}
        </div>

        {!isLoading && run && (
          <div className="sticky bottom-0 border-t bg-background/95 p-4 backdrop-blur-sm print:hidden">
            <Tooltip>
              <TooltipTrigger
                render={
                  <div className="flex cursor-not-allowed items-center gap-2 rounded-2xl border border-dashed bg-muted/30 px-4 py-3 text-sm text-muted-foreground">
                    <Lock className="size-4 shrink-0" />
                    Follow-up conversations are coming soon — start a new research above for now
                  </div>
                }
              />
              <TooltipContent>
                Each research run is currently its own thread; asking a follow-up in the same conversation isn&apos;t
                supported by the backend yet
              </TooltipContent>
            </Tooltip>
          </div>
        )}
      </div>
    </>
  );
}

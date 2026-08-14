"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, ArrowLeft, Gauge, Loader2, RotateCw } from "lucide-react";
import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { SiteHeader } from "@/components/layout/site-header";
import { ResearchStatusBadge } from "@/components/research/status-badge";

import { useResearchRun } from "@/hooks/use-research";

function useElapsed(startIso: string, active: boolean) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!active) return;
    const start = new Date(startIso).getTime();
    const tick = () => setElapsed(Math.max(0, Math.round((Date.now() - start) / 1000)));
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [startIso, active]);

  return elapsed;
}

function formatDuration(seconds: number) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

export default function ResearchDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: run, isLoading, isError } = useResearchRun(id);
  const active = run?.status === "pending" || run?.status === "running";
  const elapsed = useElapsed(run?.created_at ?? new Date().toISOString(), !!active);

  return (
    <>
      <SiteHeader title="Research" />

      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-4 p-4 md:p-6">
        <Button variant="ghost" size="sm" className="w-fit" render={<Link href="/research" />}>
          <ArrowLeft />
          Back to history
        </Button>

        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-32 w-full" />
          </div>
        ) : isError || !run ? (
          <Card>
            <CardContent className="flex flex-col items-center gap-2 py-16 text-center">
              <AlertTriangle className="size-8 text-destructive" />
              <p className="text-sm font-medium">Couldn&apos;t load this research run</p>
              <p className="text-sm text-muted-foreground">It may not exist, or you may not have access to it.</p>
            </CardContent>
          </Card>
        ) : (
          <>
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <ResearchStatusBadge status={run.status} />
                {run.quality_score != null && (
                  <Badge variant="outline" className="gap-1">
                    <Gauge className="size-3" />
                    Quality {run.quality_score.toFixed(0)}
                  </Badge>
                )}
                {run.iteration > 0 && <Badge variant="outline">Reflection pass {run.iteration}</Badge>}
              </div>
              <h1 className="text-xl font-semibold tracking-tight text-balance">{run.query}</h1>
              {run.objective && <p className="text-sm text-muted-foreground">{run.objective}</p>}
            </div>

            {active && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <Card>
                  <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
                    <Loader2 className="size-8 animate-spin text-primary" />
                    <p className="text-sm font-medium">DeepLens is researching your query…</p>
                    <p className="text-xs text-muted-foreground">
                      Planning, searching, verifying, and citing sources — {formatDuration(elapsed)} elapsed
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {run.status === "failed" && (
              <Card className="border-destructive/30">
                <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
                  <AlertTriangle className="size-8 text-destructive" />
                  <p className="text-sm font-medium">This research run failed</p>
                  {run.error && <p className="max-w-md text-sm text-muted-foreground">{run.error}</p>}
                  <Button variant="outline" size="sm" render={<Link href="/research/new" />}>
                    <RotateCw />
                    Try again
                  </Button>
                </CardContent>
              </Card>
            )}

            {run.status === "completed" && run.report && (
              <Card>
                <CardHeader className="text-xs text-muted-foreground">
                  Completed {run.completed_at && new Date(run.completed_at).toLocaleString()}
                </CardHeader>
                <CardContent>
                  <div
                    className="max-w-none space-y-4 text-sm leading-relaxed
                      [&_h1]:mt-6 [&_h1]:text-xl [&_h1]:font-semibold [&_h1]:first:mt-0
                      [&_h2]:mt-5 [&_h2]:text-lg [&_h2]:font-semibold
                      [&_h3]:mt-4 [&_h3]:text-base [&_h3]:font-semibold
                      [&_p]:leading-relaxed
                      [&_ul]:ml-5 [&_ul]:list-disc [&_ul]:space-y-1
                      [&_ol]:ml-5 [&_ol]:list-decimal [&_ol]:space-y-1
                      [&_a]:text-primary [&_a]:underline [&_a]:underline-offset-4
                      [&_code]:rounded [&_code]:bg-muted [&_code]:px-1 [&_code]:py-0.5 [&_code]:font-mono [&_code]:text-xs
                      [&_pre]:overflow-x-auto [&_pre]:rounded-lg [&_pre]:bg-muted [&_pre]:p-3
                      [&_blockquote]:border-l-2 [&_blockquote]:border-primary/40 [&_blockquote]:pl-3 [&_blockquote]:text-muted-foreground
                      [&_table]:w-full [&_table]:border-collapse [&_th]:border [&_th]:border-border [&_th]:p-2 [&_th]:text-left [&_td]:border [&_td]:border-border [&_td]:p-2
                      [&_hr]:my-6 [&_hr]:border-border"
                  >
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{run.report}</ReactMarkdown>
                  </div>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </div>
    </>
  );
}

"use client";

import { useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { CheckCircle2, Clock, FileSearch, Gauge, Sparkles, XCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { SiteHeader } from "@/components/layout/site-header";
import { ChatComposer } from "@/components/research/chat-composer";
import { ResearchStatusBadge } from "@/components/research/status-badge";
import { useCurrentUser } from "@/hooks/use-auth";
import { useCreateResearch, useRecentResearch } from "@/hooks/use-research";
import { formatDuration, formatRelativeTime } from "@/lib/format";
import { displayName } from "@/lib/user";
import { cn } from "@/lib/utils";

// recharts is a sizable dependency (~110KB) that only this card on this page
// needs — keeping it out of /dashboard's initial JS the same way mermaid and
// katex are already kept out of /research/[id]'s (see CLAUDE.md).
const StatusChart = dynamic(() => import("@/components/dashboard/status-chart").then((m) => m.StatusChart), {
  ssr: false,
  loading: () => <Skeleton className="h-full w-full" />,
});

const WELCOME_MESSAGES: ((name: string) => string)[] = [
  (name) => `Welcome aboard, ${name}`,
  (name) => `What's the agenda today, ${name}?`,
  (name) => `Good to see you back, ${name}`,
  (name) => `Ready to dig in, ${name}?`,
  (name) => `${name}, let's find some answers`,
  (name) => `Glad you're here, ${name}`,
  (name) => `Where should we start, ${name}?`,
];

export default function DashboardPage() {
  const router = useRouter();
  const { data: user } = useCurrentUser();
  // Same limit as the History page's query — shares one cached TanStack Query
  // entry so navigating between Dashboard and History is instant (no refetch)
  // instead of each page cold-fetching its own slightly different list.
  const { data: runs, isLoading } = useRecentResearch(100);
  const createResearch = useCreateResearch();
  const [query, setQuery] = useState("");

  // Chosen once per mount so the greeting changes every time the dashboard opens.
  const [welcomeIndex] = useState(() => Math.floor(Math.random() * WELCOME_MESSAGES.length));

  const handleSearchSubmit = () => {
    if (query.trim().length < 10) return;
    createResearch.mutate({ query: query.trim() });
  };

  const total = runs?.length ?? 0;
  const completed = runs?.filter((r) => r.status === "completed").length ?? 0;
  const failed = runs?.filter((r) => r.status === "failed").length ?? 0;
  const scores = runs?.map((r) => r.quality_score).filter((s): s is number => s != null) ?? [];
  const avgScore = scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : null;

  const durations =
    runs
      ?.filter((r) => r.status === "completed" && r.completed_at)
      .map((r) => (new Date(r.completed_at!).getTime() - new Date(r.created_at).getTime()) / 1000)
      .filter((seconds) => seconds > 0) ?? [];
  const avgDuration = durations.length ? durations.reduce((a, b) => a + b, 0) / durations.length : null;

  const stats = [
    { label: "Total research", value: total, icon: FileSearch, tint: "text-primary bg-primary/10" },
    { label: "Successful", value: completed, icon: CheckCircle2, tint: "text-success bg-success/10" },
    { label: "Failed", value: failed, icon: XCircle, tint: "text-destructive bg-destructive/10" },
    { label: "Average time", value: avgDuration != null ? formatDuration(avgDuration) : "—", icon: Clock, tint: "text-chart-2 bg-chart-2/10" },
    { label: "Avg. quality score", value: avgScore != null ? avgScore : "—", icon: Gauge, tint: "text-chart-4 bg-chart-4/10" },
  ];

  const chartData = [
    { name: "Pending", count: runs?.filter((r) => r.status === "pending").length ?? 0, fill: "var(--color-chart-4)" },
    { name: "Running", count: runs?.filter((r) => r.status === "running").length ?? 0, fill: "var(--color-chart-2)" },
    { name: "Completed", count: completed, fill: "var(--color-chart-3)" },
    { name: "Failed", count: failed, fill: "var(--color-chart-5)" },
  ];

  return (
    <>
      <SiteHeader title="Dashboard" />

      <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-8 p-4 md:p-8">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: "easeOut" }}
          className="relative flex flex-col justify-between gap-5 overflow-hidden rounded-2xl border bg-gradient-to-br from-primary/12 via-card to-card p-8 shadow-sm sm:flex-row sm:items-center"
        >
          <div
            aria-hidden
            className="pointer-events-none absolute -top-16 -right-16 size-56 rounded-full bg-primary/10 blur-3xl"
          />
          <div className="relative space-y-1.5">
            {user ? (
              <h1 className="text-2xl font-semibold tracking-tight text-balance">
                {WELCOME_MESSAGES[welcomeIndex](displayName(user))}
              </h1>
            ) : (
              <Skeleton className="h-8 w-64" />
            )}
            <p className="text-sm text-muted-foreground">Here&apos;s what&apos;s happening with your research.</p>
          </div>
          <Button size="lg" className="relative shadow-sm" nativeButton={false} render={<Link href="/research/new" />}>
            <Sparkles />
            New research
          </Button>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.05, ease: "easeOut" }}
        >
          <ChatComposer
            value={query}
            onChange={setQuery}
            onSubmit={handleSearchSubmit}
            isSubmitting={createResearch.isPending}
            placeholder="Search or ask DeepLens to research anything…"
          />
        </motion.div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="grid grid-cols-2 gap-4 self-start sm:grid-cols-3 lg:grid-cols-2">
            {stats.map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05, ease: "easeOut" }}
              >
                <Card className="card-hover h-full">
                  <CardHeader className="flex-row items-center justify-between space-y-0 pb-0">
                    <CardTitle className="text-xs font-medium text-muted-foreground">{stat.label}</CardTitle>
                    <span className={cn("flex size-8 items-center justify-center rounded-lg", stat.tint)}>
                      <stat.icon className="size-4" />
                    </span>
                  </CardHeader>
                  <CardContent>
                    {isLoading ? (
                      <Skeleton className="h-8 w-14" />
                    ) : (
                      <p className="text-2xl font-semibold tabular-nums">{stat.value}</p>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>

          <Card className="flex flex-col">
            <CardHeader>
              <CardTitle>Research status breakdown</CardTitle>
            </CardHeader>
            <CardContent className="flex-1">
              <div className="h-64 w-full min-w-0 sm:h-full sm:min-h-56">
                <StatusChart data={chartData} />
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Recent activity</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 4 }).map((_, index) => (
                  <Skeleton key={index} className="h-10 w-full" />
                ))}
              </div>
            ) : !runs?.length ? (
              <div className="flex flex-col items-center gap-3 py-16 text-center">
                <span className="flex size-14 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
                  <FileSearch className="size-6" />
                </span>
                <div className="space-y-1">
                  <p className="text-sm font-medium">No research yet</p>
                  <p className="text-sm text-muted-foreground">
                    Your research history will show up here once you run your first query.
                  </p>
                </div>
                <Button size="sm" nativeButton={false} render={<Link href="/research/new" />}>
                  <Sparkles />
                  Start your first research
                </Button>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Query</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Quality</TableHead>
                    <TableHead className="text-right">Created</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {runs.slice(0, 8).map((run) => (
                    <TableRow
                      key={run.id}
                      role="link"
                      aria-label={`View research: ${run.query}`}
                      className="cursor-pointer"
                      tabIndex={0}
                      onClick={() => router.push(`/research/${run.id}`)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter") router.push(`/research/${run.id}`);
                      }}
                    >
                      <TableCell className="max-w-xs truncate font-medium">{run.query}</TableCell>
                      <TableCell>
                        <ResearchStatusBadge status={run.status} />
                      </TableCell>
                      <TableCell className="tabular-nums text-muted-foreground">
                        {run.quality_score != null ? run.quality_score.toFixed(0) : "—"}
                      </TableCell>
                      <TableCell className="text-right text-muted-foreground">
                        {formatRelativeTime(run.created_at)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}

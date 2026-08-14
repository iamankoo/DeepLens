"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { CheckCircle2, FileSearch, Gauge, ListChecks, Sparkles } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { SiteHeader } from "@/components/layout/site-header";
import { ResearchStatusBadge } from "@/components/research/status-badge";
import { useCurrentUser } from "@/hooks/use-auth";
import { useRecentResearch } from "@/hooks/use-research";
import { formatRelativeTime } from "@/lib/format";
import { displayName } from "@/lib/user";
import { cn } from "@/lib/utils";

function greeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

export default function DashboardPage() {
  const router = useRouter();
  const { data: user } = useCurrentUser();
  const { data: runs, isLoading } = useRecentResearch(50);

  const total = runs?.length ?? 0;
  const completed = runs?.filter((r) => r.status === "completed").length ?? 0;
  const inProgress = runs?.filter((r) => r.status === "pending" || r.status === "running").length ?? 0;
  const scores = runs?.map((r) => r.quality_score).filter((s): s is number => s != null) ?? [];
  const avgScore = scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : null;

  const stats = [
    { label: "Total research runs", value: total, icon: FileSearch, tint: "text-primary bg-primary/10" },
    { label: "Completed", value: completed, icon: CheckCircle2, tint: "text-success bg-success/10" },
    { label: "In progress", value: inProgress, icon: ListChecks, tint: "text-chart-2 bg-chart-2/10" },
    { label: "Avg. quality score", value: avgScore != null ? avgScore : "—", icon: Gauge, tint: "text-chart-4 bg-chart-4/10" },
  ];

  const chartData = [
    { name: "Pending", count: runs?.filter((r) => r.status === "pending").length ?? 0, fill: "var(--color-chart-4)" },
    { name: "Running", count: runs?.filter((r) => r.status === "running").length ?? 0, fill: "var(--color-chart-2)" },
    { name: "Completed", count: completed, fill: "var(--color-chart-3)" },
    { name: "Failed", count: runs?.filter((r) => r.status === "failed").length ?? 0, fill: "var(--color-chart-5)" },
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
            <p className="text-sm text-muted-foreground">
              {greeting()}
              {user ? `, ${displayName(user)}` : ""}
            </p>
            <h1 className="text-2xl font-semibold tracking-tight text-balance">Welcome back to DeepLens</h1>
            <p className="text-sm text-muted-foreground">Here&apos;s what&apos;s happening with your research.</p>
          </div>
          <Button size="lg" className="relative shadow-sm" nativeButton={false} render={<Link href="/research/new" />}>
            <Sparkles />
            New research
          </Button>
        </motion.div>

        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.05, ease: "easeOut" }}
            >
              <Card className="card-hover">
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

        {total > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Research status breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-56 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ left: -20 }}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-border" vertical={false} />
                    <XAxis dataKey="name" tickLine={false} axisLine={false} className="text-xs fill-muted-foreground" />
                    <YAxis allowDecimals={false} tickLine={false} axisLine={false} className="text-xs fill-muted-foreground" />
                    <Tooltip
                      cursor={{ fill: "var(--color-muted)" }}
                      contentStyle={{
                        background: "var(--color-popover)",
                        border: "1px solid var(--color-border)",
                        borderRadius: "var(--radius-lg)",
                        fontSize: 12,
                      }}
                    />
                    <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                      {chartData.map((entry) => (
                        <Cell key={entry.name} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}

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

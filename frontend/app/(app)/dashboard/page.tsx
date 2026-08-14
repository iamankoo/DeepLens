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
    { label: "Total research runs", value: total, icon: FileSearch },
    { label: "Completed", value: completed, icon: CheckCircle2 },
    { label: "In progress", value: inProgress, icon: ListChecks },
    { label: "Avg. quality score", value: avgScore != null ? avgScore : "—", icon: Gauge },
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

      <div className="flex flex-1 flex-col gap-6 p-4 md:p-6">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: "easeOut" }}
          className="flex flex-col justify-between gap-4 rounded-xl border bg-gradient-to-br from-primary/10 via-card to-card p-6 sm:flex-row sm:items-center"
        >
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">
              {greeting()}
              {user ? `, ${user.email.split("@")[0]}` : ""}
            </p>
            <h1 className="text-xl font-semibold tracking-tight">Welcome back to DeepLens</h1>
          </div>
          <Button size="lg" render={<Link href="/research/new" />}>
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
              <Card size="sm">
                <CardHeader className="flex-row items-center justify-between space-y-0 pb-0">
                  <CardTitle className="text-xs font-medium text-muted-foreground">{stat.label}</CardTitle>
                  <stat.icon className="size-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  {isLoading ? (
                    <Skeleton className="h-7 w-12" />
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
              <div className="flex flex-col items-center gap-2 py-12 text-center">
                <FileSearch className="size-8 text-muted-foreground" />
                <p className="text-sm font-medium">No research yet</p>
                <p className="text-sm text-muted-foreground">
                  Your research history will show up here once you run your first query.
                </p>
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

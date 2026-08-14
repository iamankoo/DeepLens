"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FileSearch, FileText, Plus, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { SiteHeader } from "@/components/layout/site-header";
import { ResearchStatusBadge } from "@/components/research/status-badge";
import { useRecentResearch } from "@/hooks/use-research";
import { formatRelativeTime } from "@/lib/format";

export default function ResearchHistoryPage() {
  const router = useRouter();
  const { data: runs, isLoading } = useRecentResearch(100);
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    if (!runs) return [];
    const term = search.trim().toLowerCase();
    return term ? runs.filter((r) => r.query.toLowerCase().includes(term)) : runs;
  }, [runs, search]);

  return (
    <>
      <SiteHeader title="History" />

      <div className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-5 p-4 md:p-8">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative w-full max-w-sm">
            <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search your research…"
              className="pl-8"
            />
          </div>
          <Button nativeButton={false} render={<Link href="/research/new" />}>
            <Plus />
            New research
          </Button>
        </div>

        <Card>
          <CardContent>
            {isLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 6 }).map((_, index) => (
                  <Skeleton key={index} className="h-10 w-full" />
                ))}
              </div>
            ) : !filtered.length ? (
              <div className="flex flex-col items-center gap-3 py-16 text-center">
                <span className="flex size-14 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
                  <FileSearch className="size-6" />
                </span>
                <div className="space-y-1">
                  <p className="text-sm font-medium">{search ? "No matching research" : "No research yet"}</p>
                  <p className="text-sm text-muted-foreground">
                    {search ? "Try a different search term." : "Start your first research to see it here."}
                  </p>
                </div>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Query</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Quality</TableHead>
                    <TableHead>Timestamp</TableHead>
                    <TableHead className="text-right">Report</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered.map((run) => (
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
                      <TableCell className="max-w-sm truncate font-medium">{run.query}</TableCell>
                      <TableCell>
                        <ResearchStatusBadge status={run.status} />
                      </TableCell>
                      <TableCell className="tabular-nums text-muted-foreground">
                        {run.quality_score != null ? run.quality_score.toFixed(0) : "—"}
                      </TableCell>
                      <TableCell className="text-muted-foreground">{formatRelativeTime(run.created_at)}</TableCell>
                      <TableCell className="text-right">
                        {run.status === "completed" ? (
                          <Button
                            variant="outline"
                            size="sm"
                            nativeButton={false}
                            render={<Link href={`/research/${run.id}`} />}
                            onClick={(event) => event.stopPropagation()}
                          >
                            <FileText />
                            Report
                          </Button>
                        ) : (
                          <span className="text-xs text-muted-foreground/60">—</span>
                        )}
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

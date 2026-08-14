"use client";

import Link from "next/link";
import { Bell, CheckCircle2, XCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useNotifications } from "@/hooks/use-notifications";
import { formatRelativeTime } from "@/lib/format";
import { cn } from "@/lib/utils";

export function NotificationsMenu() {
  const { items, unreadCount, markSeen } = useNotifications();

  return (
    <DropdownMenu onOpenChange={(open) => !open && markSeen()}>
      <DropdownMenuTrigger
        render={
          <Button variant="ghost" size="icon-sm" className="relative">
            <Bell />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 flex size-2 rounded-full bg-primary" />
            )}
            <span className="sr-only">Notifications</span>
          </Button>
        }
      />
      <DropdownMenuContent align="end" className="w-80">
        <DropdownMenuLabel>Notifications</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {!items.length ? (
          <p className="px-2 py-6 text-center text-sm text-muted-foreground">
            You&apos;ll see research updates here.
          </p>
        ) : (
          items.map((item) => (
            <DropdownMenuItem key={item.run.id} render={<Link href={`/research/${item.run.id}`} />} className="items-start gap-2 py-2">
              {item.run.status === "completed" ? (
                <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" />
              ) : (
                <XCircle className="mt-0.5 size-4 shrink-0 text-destructive" />
              )}
              <span className="flex-1 space-y-0.5">
                <span className="block truncate text-sm">
                  Research {item.run.status === "completed" ? "completed" : "failed"}
                </span>
                <span className="block truncate text-xs text-muted-foreground">{item.run.query}</span>
              </span>
              <span className={cn("shrink-0 text-xs text-muted-foreground", item.isUnread && "font-medium text-foreground")}>
                {formatRelativeTime(item.run.completed_at!)}
              </span>
            </DropdownMenuItem>
          ))
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

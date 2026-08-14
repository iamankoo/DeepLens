"use client";

import { useMemo } from "react";
import { create } from "zustand";
import { persist } from "zustand/middleware";

import { useRecentResearch } from "@/hooks/use-research";
import type { ResearchRunSummary } from "@/types/research";

interface NotificationsState {
  lastSeenAt: string;
  markSeen: () => void;
}

// Notifications are derived from real research-run state transitions
// (completed/failed), not a fabricated feed — there's no backend
// notifications table yet, so this stays a thin read of data already
// being polled for the dashboard/history views.
const useNotificationsStore = create<NotificationsState>()(
  persist(
    (set) => ({
      lastSeenAt: new Date(0).toISOString(),
      markSeen: () => set({ lastSeenAt: new Date().toISOString() }),
    }),
    { name: "deeplens-notifications" }
  )
);

export interface NotificationItem {
  run: ResearchRunSummary;
  isUnread: boolean;
}

export function useNotifications() {
  const { data: runs } = useRecentResearch(20);
  const lastSeenAt = useNotificationsStore((state) => state.lastSeenAt);
  const markSeen = useNotificationsStore((state) => state.markSeen);

  const items = useMemo<NotificationItem[]>(() => {
    if (!runs) return [];
    const lastSeenTime = new Date(lastSeenAt).getTime();
    return runs
      .filter((run) => run.status === "completed" || run.status === "failed")
      .filter((run) => run.completed_at)
      .sort((a, b) => new Date(b.completed_at!).getTime() - new Date(a.completed_at!).getTime())
      .slice(0, 10)
      .map((run) => ({ run, isUnread: new Date(run.completed_at!).getTime() > lastSeenTime }));
  }, [runs, lastSeenAt]);

  const unreadCount = items.filter((item) => item.isUnread).length;

  return { items, unreadCount, markSeen };
}

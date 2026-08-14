"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { researchService } from "@/services/research-service";
import { useAuthStore } from "@/stores/auth-store";
import { getApiErrorMessage } from "@/lib/api-error";
import type { CreateResearchPayload } from "@/types/research";

const ACTIVE_STATUSES = new Set(["pending", "running"]);

export function useRecentResearch(limit = 8) {
  const accessToken = useAuthStore((state) => state.accessToken);

  return useQuery({
    queryKey: ["research", "list", { limit }],
    queryFn: () => researchService.list({ limit }),
    enabled: !!accessToken,
    staleTime: 15 * 1000,
    // Keeps the dashboard/history "in progress" rows moving without a manual refresh.
    refetchInterval: (query) => (query.state.data?.some((r) => ACTIVE_STATUSES.has(r.status)) ? 4000 : false),
  });
}

export function useResearchRun(id: string) {
  return useQuery({
    queryKey: ["research", "detail", id],
    queryFn: () => researchService.get(id),
    refetchInterval: (query) => (query.state.data && ACTIVE_STATUSES.has(query.state.data.status) ? 2500 : false),
  });
}

export function useCreateResearch() {
  const router = useRouter();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateResearchPayload) => researchService.create(payload),
    onSuccess: (run) => {
      queryClient.invalidateQueries({ queryKey: ["research", "list"] });
      toast.success("Research started");
      router.push(`/research/${run.id}`);
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Could not start research"));
    },
  });
}

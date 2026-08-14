import { apiClient } from "@/lib/api-client";
import type { CreateResearchPayload, ResearchRunDetail, ResearchRunSummary } from "@/types/research";

export const researchService = {
  async list(params?: { limit?: number; offset?: number }): Promise<ResearchRunSummary[]> {
    const { data } = await apiClient.get<ResearchRunSummary[]>("/research", { params });
    return data;
  },

  async get(id: string): Promise<ResearchRunDetail> {
    const { data } = await apiClient.get<ResearchRunDetail>(`/research/${id}`);
    return data;
  },

  async create(payload: CreateResearchPayload): Promise<ResearchRunSummary> {
    const { data } = await apiClient.post<ResearchRunSummary>("/research", payload);
    return data;
  },
};

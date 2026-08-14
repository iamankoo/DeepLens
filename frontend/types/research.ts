export type ResearchStatus = "pending" | "running" | "completed" | "failed";

export interface ResearchRunSummary {
  id: string;
  query: string;
  status: ResearchStatus;
  quality_score: number | null;
  created_at: string;
  completed_at: string | null;
}

export interface ResearchRunDetail extends ResearchRunSummary {
  objective: string | null;
  report: string | null;
  iteration: number;
  error: string | null;
}

export interface CreateResearchPayload {
  query: string;
}

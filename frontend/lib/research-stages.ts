import {
  BookOpen,
  Brain,
  CheckCheck,
  FileSearch,
  Globe,
  ListChecks,
  PenLine,
  Quote,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

export interface StageMeta {
  key: string;
  label: string;
  icon: LucideIcon;
}

// Mirrors backend/app/workflows/research_workflow.py's node order exactly —
// `current_step` on a ResearchRun is the raw LangGraph node name, reported
// live via WorkflowManager's on_step callback (see backend CLAUDE.md notes).
// This is the only place that order/labels are defined for the UI.
export const RESEARCH_STAGES: StageMeta[] = [
  { key: "planner", label: "Planning research", icon: Brain },
  { key: "memory_search", label: "Checking memory", icon: Sparkles },
  { key: "search", label: "Searching the web", icon: Globe },
  { key: "ranking", label: "Ranking sources", icon: SlidersHorizontal },
  { key: "chunking", label: "Processing sources", icon: FileSearch },
  { key: "retrieval", label: "Retrieving context", icon: BookOpen },
  { key: "writer", label: "Writing report", icon: PenLine },
  { key: "verification", label: "Verifying claims", icon: ShieldCheck },
  { key: "rewrite", label: "Refining weak sections", icon: ListChecks },
  { key: "citation", label: "Adding citations", icon: Quote },
  { key: "reflection", label: "Reviewing quality", icon: CheckCheck },
];

const STAGE_INDEX = new Map(RESEARCH_STAGES.map((stage, index) => [stage.key, index]));

export function stageIndex(step: string | null): number {
  if (!step) return -1;
  return STAGE_INDEX.get(step) ?? -1;
}

export function stageLabel(step: string | null): string {
  if (!step) return "Getting started";
  const stage = RESEARCH_STAGES.find((s) => s.key === step);
  return stage?.label ?? "Working";
}

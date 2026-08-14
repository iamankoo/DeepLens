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

// A curated 5-6 stop subset of RESEARCH_STAGES for the milestone-road
// visualization — the full 11-node list is too dense to show as signboards.
export const ROBOT_MILESTONE_KEYS = ["planner", "search", "ranking", "writer", "verification", "citation"];

export const ROBOT_MILESTONES: StageMeta[] = ROBOT_MILESTONE_KEYS.map(
  (key) => RESEARCH_STAGES.find((stage) => stage.key === key)!
);

function shortTopic(query: string, maxLength = 48): string {
  const trimmed = query.trim().replace(/\s+/g, " ");
  if (trimmed.length <= maxLength) return trimmed;
  return `${trimmed.slice(0, maxLength).trimEnd()}…`;
}

// Contextual, per-stage status copy that names the user's actual topic
// instead of a generic "Loading…" — the topic is the user's own query text,
// not a fabricated summary, so no extra LLM call is needed to produce it.
export function stageStatusText(step: string | null, query: string): string {
  const topic = shortTopic(query);

  switch (step) {
    case "planner":
      return `Planning the research structure for "${topic}"…`;
    case "memory_search":
      return `Checking memory for prior research on "${topic}"…`;
    case "search":
      return `Searching trusted sources about "${topic}"…`;
    case "ranking":
      return `Ranking the most relevant sources on "${topic}"…`;
    case "chunking":
      return `Processing source material on "${topic}"…`;
    case "retrieval":
      return `Collecting supporting evidence for "${topic}"…`;
    case "writer":
      return `Writing the first draft covering "${topic}"…`;
    case "verification":
      return `Verifying claims about "${topic}" against sources…`;
    case "rewrite":
      return `Refining weaker sections of the "${topic}" report…`;
    case "citation":
      return `Adding citations to the "${topic}" report…`;
    case "reflection":
      return `Reviewing overall quality of the "${topic}" report…`;
    default:
      return `Getting started on "${topic}"…`;
  }
}

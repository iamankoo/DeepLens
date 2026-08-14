import { Sparkles } from "lucide-react";

export function UserMessage({ query }: { query: string }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[80%] rounded-2xl rounded-tr-md bg-primary px-4 py-2.5 text-sm text-primary-foreground shadow-sm">
        {query}
      </div>
    </div>
  );
}

export function AssistantAvatar() {
  return (
    <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
      <Sparkles className="size-3.5" />
    </span>
  );
}

export function AssistantMessage({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex gap-3">
      <AssistantAvatar />
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}

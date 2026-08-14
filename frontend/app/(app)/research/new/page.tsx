"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

import { SiteHeader } from "@/components/layout/site-header";
import { ChatComposer } from "@/components/research/chat-composer";
import { useCreateResearch } from "@/hooks/use-research";
import { useCurrentUser } from "@/hooks/use-auth";

const EXAMPLES = [
  "Compare the safety profiles of mRNA and viral-vector vaccine platforms.",
  "What are the strongest arguments for and against carbon border taxes?",
  "Summarize the current state of solid-state battery commercialization.",
  "What are the leading approaches to fusion energy and how close are they to commercial viability?",
];

export default function NewResearchPage() {
  const createResearch = useCreateResearch();
  const { data: user } = useCurrentUser();
  const [value, setValue] = useState("");

  const handleSubmit = () => {
    if (value.trim().length < 10) return;
    createResearch.mutate({ query: value.trim() });
  };

  return (
    <>
      <SiteHeader title="New research" />

      <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col items-center justify-center gap-8 p-4 md:p-6">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          className="w-full space-y-6 text-center"
        >
          <span className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 text-primary ring-1 ring-primary/20">
            <Sparkles className="size-6" />
          </span>
          <div className="space-y-1.5">
            <h1 className="text-2xl font-semibold tracking-tight text-balance">
              {user ? `What should DeepLens research, ${user.email.split("@")[0]}?` : "What should DeepLens research?"}
            </h1>
            <p className="text-sm text-muted-foreground">
              Ask anything — DeepLens plans, searches, verifies, and cites its way to an answer.
            </p>
          </div>

          <ChatComposer
            value={value}
            onChange={setValue}
            onSubmit={handleSubmit}
            isSubmitting={createResearch.isPending}
            autoFocus
          />

          <div className="flex flex-wrap justify-center gap-2">
            {EXAMPLES.map((example) => (
              <button
                key={example}
                type="button"
                onClick={() => setValue(example)}
                className="rounded-full border px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-ring/50 hover:bg-muted hover:text-foreground"
              >
                {example}
              </button>
            ))}
          </div>
        </motion.div>
      </div>
    </>
  );
}

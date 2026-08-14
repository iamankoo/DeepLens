"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Sparkles } from "lucide-react";

import { SiteHeader } from "@/components/layout/site-header";
import { ChatComposer } from "@/components/research/chat-composer";
import { useCreateResearch } from "@/hooks/use-research";
import { useCurrentUser } from "@/hooks/use-auth";
import { displayName } from "@/lib/user";

const SUGGESTION_POOL = [
  "Compare the safety profiles of mRNA and viral-vector vaccine platforms.",
  "What are the strongest arguments for and against carbon border taxes?",
  "Summarize the current state of solid-state battery commercialization.",
  "What are the leading approaches to fusion energy and how close are they to commercial viability?",
  "How is retrieval-augmented generation changing enterprise AI adoption?",
  "What does current research say about the four-day work week's effect on productivity?",
  "Compare the manufacturing growth strategies of India and Vietnam.",
  "What are the most promising approaches to industrial-scale carbon capture?",
  "How are large language models evaluated for factual reliability?",
  "What is the state of quantum error correction and how far is it from practical use?",
];

const SUGGESTION_COUNT = 5;
const ROTATE_INTERVAL_MS = 5000;

export default function NewResearchPage() {
  const createResearch = useCreateResearch();
  const { data: user } = useCurrentUser();
  const [value, setValue] = useState("");
  const [suggestions, setSuggestions] = useState(() => SUGGESTION_POOL.slice(0, SUGGESTION_COUNT));

  const slotRef = useRef(0);
  const cursorRef = useRef(SUGGESTION_COUNT);

  useEffect(() => {
    const interval = setInterval(() => {
      setSuggestions((prev) => {
        const next = [...prev];
        next[slotRef.current] = SUGGESTION_POOL[cursorRef.current % SUGGESTION_POOL.length];
        cursorRef.current += 1;
        slotRef.current = (slotRef.current + 1) % SUGGESTION_COUNT;
        return next;
      });
    }, ROTATE_INTERVAL_MS);

    return () => clearInterval(interval);
  }, []);

  const startResearch = (query: string) => {
    const trimmed = query.trim();
    if (trimmed.length < 10 || createResearch.isPending) return;
    createResearch.mutate({ query: trimmed });
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
              {user ? `What should DeepLens research, ${displayName(user)}?` : "What should DeepLens research?"}
            </h1>
            <p className="text-sm text-muted-foreground">
              Ask anything — DeepLens plans, searches, verifies, and cites its way to an answer.
            </p>
          </div>

          <ChatComposer
            value={value}
            onChange={setValue}
            onSubmit={() => startResearch(value)}
            isSubmitting={createResearch.isPending}
            autoFocus
          />

          <div className="flex flex-wrap justify-center gap-2">
            <AnimatePresence mode="popLayout" initial={false}>
              {suggestions.map((suggestion) => (
                <motion.button
                  key={suggestion}
                  type="button"
                  layout
                  initial={{ opacity: 0, y: 4, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ duration: 0.3, ease: "easeOut" }}
                  onClick={() => startResearch(suggestion)}
                  disabled={createResearch.isPending}
                  className="rounded-full border px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-ring/50 hover:bg-muted hover:text-foreground disabled:pointer-events-none disabled:opacity-50"
                >
                  {suggestion}
                </motion.button>
              ))}
            </AnimatePresence>
          </div>
        </motion.div>
      </div>
    </>
  );
}

"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm } from "react-hook-form";
import { motion } from "framer-motion";
import { Loader2, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, FieldError } from "@/components/ui/field";
import { Textarea } from "@/components/ui/textarea";
import { SiteHeader } from "@/components/layout/site-header";
import { useCreateResearch } from "@/hooks/use-research";
import { newResearchSchema, type NewResearchFormValues } from "@/lib/validations/research";

const EXAMPLES = [
  "Compare the safety profiles of mRNA and viral-vector vaccine platforms.",
  "What are the strongest arguments for and against carbon border taxes?",
  "Summarize the current state of solid-state battery commercialization.",
];

export default function NewResearchPage() {
  const createResearch = useCreateResearch();
  const form = useForm<NewResearchFormValues>({
    resolver: zodResolver(newResearchSchema),
    defaultValues: { query: "" },
  });

  return (
    <>
      <SiteHeader title="New research" />

      <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col justify-center gap-6 p-4 md:p-6">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: "easeOut" }}
        >
          <Card>
            <CardHeader>
              <span className="flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <Sparkles className="size-5" />
              </span>
              <CardTitle className="mt-3">What should DeepLens research?</CardTitle>
              <CardDescription>
                Describe your question in as much detail as you like — DeepLens will plan, search, verify, and
                cite its way to a report.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={form.handleSubmit((values) => createResearch.mutate(values))} noValidate>
                <Controller
                  name="query"
                  control={form.control}
                  render={({ field, fieldState }) => (
                    <Field data-invalid={fieldState.invalid}>
                      <Textarea
                        {...field}
                        rows={6}
                        placeholder="e.g. What are the leading approaches to fusion energy and how close are they to commercial viability?"
                        aria-invalid={fieldState.invalid}
                        autoFocus
                      />
                      <FieldError errors={[fieldState.error]} />
                    </Field>
                  )}
                />

                <div className="mt-4 flex items-center justify-between">
                  <p className="text-xs text-muted-foreground">
                    Typically takes a few minutes depending on depth and source availability.
                  </p>
                  <Button type="submit" disabled={createResearch.isPending}>
                    {createResearch.isPending && <Loader2 className="size-4 animate-spin" />}
                    Start research
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </motion.div>

        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => form.setValue("query", example, { shouldValidate: true })}
              className="rounded-full border px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-ring/50 hover:text-foreground"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </>
  );
}

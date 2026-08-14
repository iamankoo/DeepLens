"use client";

import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import Link from "next/link";

const HIGHLIGHTS = [
  "Multi-agent planning that scopes a research objective before it searches",
  "Every claim traced back to a source, with citation-level verification",
  "A reflection loop that re-checks and rewrites weak sections automatically",
];

export function AuthShell({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="grid min-h-svh lg:grid-cols-2">
      <div className="relative hidden flex-col justify-between overflow-hidden bg-sidebar p-10 text-sidebar-foreground lg:flex">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,color-mix(in_oklch,var(--primary),transparent_78%),transparent_55%),radial-gradient(circle_at_80%_75%,color-mix(in_oklch,var(--chart-2),transparent_82%),transparent_55%)]"
        />
        <Link href="/" className="relative z-10 flex items-center gap-2 text-lg font-semibold">
          <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Sparkles className="size-4" />
          </span>
          DeepLens
        </Link>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="relative z-10 max-w-md space-y-6"
        >
          <p className="text-2xl leading-snug font-medium text-balance">
            Deep research, done properly — planned, verified, and cited.
          </p>
          <ul className="space-y-3">
            {HIGHLIGHTS.map((item) => (
              <li key={item} className="flex items-start gap-2.5 text-sm text-sidebar-foreground/75">
                <span className="mt-2 size-1.5 shrink-0 rounded-full bg-primary" />
                {item}
              </li>
            ))}
          </ul>
        </motion.div>

        <p className="relative z-10 text-xs text-sidebar-foreground/50">
          &copy; {new Date().getFullYear()} DeepLens. All rights reserved.
        </p>
      </div>

      <div className="flex items-center justify-center p-6 sm:p-10">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: "easeOut" }}
          className="w-full max-w-sm space-y-8"
        >
          <Link href="/" className="flex items-center gap-2 text-lg font-semibold lg:hidden">
            <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Sparkles className="size-4" />
            </span>
            DeepLens
          </Link>

          <div className="space-y-1.5">
            <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
            <p className="text-sm text-muted-foreground">{description}</p>
          </div>

          {children}
        </motion.div>
      </div>
    </div>
  );
}

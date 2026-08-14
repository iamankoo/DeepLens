"use client";

import { useEffect, useId, useState } from "react";
import { useTheme } from "next-themes";

let mermaidPromise: Promise<typeof import("mermaid")> | null = null;

export function MermaidDiagram({ chart }: { chart: string }) {
  const id = useId().replace(/:/g, "-");
  const { resolvedTheme } = useTheme();
  const [svg, setSvg] = useState<string | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function render() {
      if (!mermaidPromise) mermaidPromise = import("mermaid");
      const { default: mermaid } = await mermaidPromise;
      mermaid.initialize({
        startOnLoad: false,
        theme: resolvedTheme === "dark" ? "dark" : "default",
        securityLevel: "strict",
        fontFamily: "inherit",
      });
      try {
        const { svg: rendered } = await mermaid.render(`mermaid-${id}`, chart);
        if (!cancelled) setSvg(rendered);
      } catch {
        if (!cancelled) setError(true);
      }
    }

    render();
    return () => {
      cancelled = true;
    };
  }, [chart, id, resolvedTheme]);

  if (error) {
    return (
      <pre className="overflow-x-auto rounded-lg bg-muted p-3 text-xs text-muted-foreground">{chart}</pre>
    );
  }

  if (!svg) {
    return <div className="h-32 w-full animate-pulse rounded-lg bg-muted" />;
  }

  return (
    <div
      className="flex justify-center overflow-x-auto rounded-lg border bg-card p-4 [&_svg]:mx-auto"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}

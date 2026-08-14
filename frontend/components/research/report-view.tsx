"use client";

import { useMemo, useState } from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import { Check, ChevronDown, Copy, Download, ExternalLink, Link2, Printer } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { CodeBlock } from "@/components/research/code-block";
import { headingId } from "@/lib/slug";
import { cn } from "@/lib/utils";

// backend/app/agents/writer_agent.py appends "\n\n---\n\n# References\n\n"
// verbatim, but the citation-injection pass that runs afterward can append
// an inline "(Source, n.d.)" citation onto that "---" or "# References"
// line itself — so this matches loosely (arbitrary trailing text on both
// lines) rather than the exact literal separator.
const REFERENCES_PATTERN = /\n\n-{3,}[^\n]*\n\n#{1,2}\s*References[^\n]*\n\n/;

function extractHeadings(markdown: string) {
  return markdown
    .split("\n")
    .filter((line) => /^#{1,3}\s+/.test(line))
    .map((line) => {
      const match = /^(#{1,3})\s+(.+)$/.exec(line);
      const level = match![1].length;
      const text = match![2].trim();
      return { level, text, id: headingId(text) };
    });
}

const proseClassName = cn(
  "max-w-none space-y-4 text-sm leading-relaxed",
  "[&_h1]:mt-8 [&_h1]:scroll-mt-20 [&_h1]:text-xl [&_h1]:font-semibold [&_h1]:first:mt-0",
  "[&_h2]:mt-6 [&_h2]:scroll-mt-20 [&_h2]:text-lg [&_h2]:font-semibold",
  "[&_h3]:mt-5 [&_h3]:scroll-mt-20 [&_h3]:text-base [&_h3]:font-semibold",
  "[&_p]:leading-relaxed",
  "[&_ul]:ml-5 [&_ul]:list-disc [&_ul]:space-y-1",
  "[&_ol]:ml-5 [&_ol]:list-decimal [&_ol]:space-y-1",
  "[&_a]:text-primary [&_a]:underline [&_a]:underline-offset-4 [&_a]:break-words",
  "[&_code:not(.hljs)]:rounded [&_code:not(.hljs)]:bg-muted [&_code:not(.hljs)]:px-1 [&_code:not(.hljs)]:py-0.5 [&_code:not(.hljs)]:font-mono [&_code:not(.hljs)]:text-xs",
  "[&_blockquote]:border-l-2 [&_blockquote]:border-primary/40 [&_blockquote]:pl-3 [&_blockquote]:text-muted-foreground",
  "[&_table]:w-full [&_table]:border-collapse [&_th]:border [&_th]:border-border [&_th]:p-2 [&_th]:text-left [&_td]:border [&_td]:border-border [&_td]:p-2",
  "[&_hr]:my-6 [&_hr]:border-border"
);

const markdownComponents: Components = {
  h1: ({ children }) => <h1 id={headingId(children)}>{children}</h1>,
  h2: ({ children }) => <h2 id={headingId(children)}>{children}</h2>,
  h3: ({ children }) => <h3 id={headingId(children)}>{children}</h3>,
  code: ({ className, children }) => {
    const isBlock = /language-/.test(className ?? "");
    if (!isBlock) {
      return <code className={className}>{children}</code>;
    }
    return <CodeBlock className={className}>{String(children)}</CodeBlock>;
  },
  pre: ({ children }) => <>{children}</>,
};

export function ReportView({
  report,
  query,
  runId,
}: {
  report: string;
  query: string;
  runId: string;
}) {
  const [copied, setCopied] = useState(false);
  const [referencesOpen, setReferencesOpen] = useState(true);

  const { body, references } = useMemo(() => {
    const match = report.match(REFERENCES_PATTERN);
    if (!match || match.index === undefined) return { body: report, references: null };
    return {
      body: report.slice(0, match.index),
      references: report
        .slice(match.index + match[0].length)
        .split("\n\n")
        .map((r) => r.trim())
        .filter(Boolean),
    };
  }, [report]);

  const headings = useMemo(() => extractHeadings(body), [body]);

  const handleCopy = () => {
    navigator.clipboard.writeText(report);
    setCopied(true);
    toast.success("Report copied to clipboard");
    setTimeout(() => setCopied(false), 1500);
  };

  const handleExportMarkdown = () => {
    const blob = new Blob([report], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `deeplens-${runId}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    toast.success("Link copied to clipboard");
  };

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_14rem]">
      <div id="report-print-content" className="min-w-0 space-y-4">
        <h1 className="hidden text-xl font-semibold print:block">{query}</h1>
        <div className="flex flex-wrap items-center gap-1.5 print:hidden">
          <Button variant="outline" size="sm" onClick={handleCopy}>
            {copied ? <Check className="text-success" /> : <Copy />}
            Copy
          </Button>
          <Button variant="outline" size="sm" onClick={handleExportMarkdown}>
            <Download />
            Export .md
          </Button>
          <Button variant="outline" size="sm" onClick={() => window.print()}>
            <Printer />
            Print / PDF
          </Button>
          <Button variant="outline" size="sm" onClick={handleShare}>
            <Link2 />
            Share
          </Button>
        </div>

        <div className={proseClassName}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm, remarkMath]}
            rehypePlugins={[rehypeKatex]}
            components={markdownComponents}
          >
            {body}
          </ReactMarkdown>
        </div>

        {references && references.length > 0 && (
          <div className="rounded-xl border">
            <button
              type="button"
              onClick={() => setReferencesOpen((v) => !v)}
              className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium"
            >
              <span>References ({references.length})</span>
              <ChevronDown className={cn("size-4 text-muted-foreground transition-transform", referencesOpen && "rotate-180")} />
            </button>
            {referencesOpen && (
              <ol className="space-y-2 border-t p-4 pt-3">
                {references.map((reference, index) => (
                  <li key={index} className="flex gap-2.5 rounded-lg bg-muted/40 p-2.5 text-xs leading-relaxed">
                    <span className="shrink-0 font-mono text-muted-foreground">[{index + 1}]</span>
                    <span className="min-w-0 flex-1 break-words">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{reference}</ReactMarkdown>
                    </span>
                    <ExternalLink className="mt-0.5 size-3 shrink-0 text-muted-foreground" />
                  </li>
                ))}
              </ol>
            )}
          </div>
        )}
      </div>

      {headings.length > 1 && (
        <nav className="hidden lg:block print:hidden">
          <div className="sticky top-20 space-y-2">
            <p className="text-xs font-medium text-muted-foreground">On this page</p>
            <ul className="space-y-1 border-l text-xs">
              {headings.map((heading) => (
                <li key={heading.id}>
                  <a
                    href={`#${heading.id}`}
                    className={cn(
                      "block truncate border-l-2 border-transparent py-1 text-muted-foreground transition-colors hover:border-primary hover:text-foreground",
                      heading.level === 1 && "pl-3 font-medium",
                      heading.level === 2 && "pl-5",
                      heading.level === 3 && "pl-7"
                    )}
                  >
                    {heading.text}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </nav>
      )}
    </div>
  );
}

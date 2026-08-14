"use client";

import { useCallback, useRef } from "react";
import { useDropzone } from "react-dropzone";
import { ArrowUp, Globe, Layers, Loader2, Paperclip, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { FileAttachmentList } from "@/components/research/file-attachment-list";
import { useFileAttachments } from "@/hooks/use-file-attachments";
import { cn } from "@/lib/utils";

const MODES = [
  { value: "web", label: "Web", icon: Globe, available: true },
  { value: "hybrid", label: "Hybrid", icon: Layers, available: false },
] as const;

interface ChatComposerProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  isSubmitting?: boolean;
  autoFocus?: boolean;
  placeholder?: string;
  maxLength?: number;
}

export function ChatComposer({
  value,
  onChange,
  onSubmit,
  isSubmitting,
  autoFocus,
  placeholder = "Ask DeepLens to research anything…",
  maxLength = 2000,
}: ChatComposerProps) {
  const { files, addFiles, removeFile } = useFileAttachments();
  const inputRef = useRef<HTMLInputElement>(null);

  const onDrop = useCallback((accepted: File[]) => addFiles(accepted), [addFiles]);
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    noClick: true,
    noKeyboard: true,
  });

  const canSubmit = value.trim().length >= 10 && !isSubmitting;

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (canSubmit) onSubmit();
    }
  };

  const handlePaste = (event: React.ClipboardEvent<HTMLTextAreaElement>) => {
    const pastedFiles = Array.from(event.clipboardData.files);
    if (pastedFiles.length) {
      addFiles(pastedFiles);
    }
  };

  return (
    <div
      {...getRootProps()}
      className={cn(
        "relative rounded-2xl border bg-card shadow-sm ring-1 ring-foreground/5 transition-all focus-within:ring-2 focus-within:ring-primary/30",
        isDragActive && "border-primary ring-2 ring-primary/40"
      )}
    >
      <input {...getInputProps()} ref={inputRef} />

      {isDragActive && (
        <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center rounded-2xl bg-primary/5 text-sm font-medium text-primary backdrop-blur-[1px]">
          Drop files to attach
        </div>
      )}

      <FileAttachmentList files={files} onRemove={removeFile} />

      <Textarea
        value={value}
        onChange={(event) => onChange(event.target.value.slice(0, maxLength))}
        onKeyDown={handleKeyDown}
        onPaste={handlePaste}
        placeholder={placeholder}
        autoFocus={autoFocus}
        disabled={isSubmitting}
        rows={1}
        maxLength={maxLength}
        className="max-h-64 min-h-14 resize-none border-none bg-transparent px-4 py-3.5 text-base shadow-none focus-visible:ring-0 md:text-base"
      />

      <div className="flex items-center justify-between gap-2 px-3 pb-3">
        <div className="flex items-center gap-1.5">
          <Tooltip>
            <TooltipTrigger
              render={
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  onClick={() => inputRef.current?.click()}
                  aria-label="Attach files"
                >
                  <Paperclip />
                </Button>
              }
            />
            <TooltipContent>Attach documents (coming soon)</TooltipContent>
          </Tooltip>

          <div className="mx-1 h-4 w-px bg-border" />

          {MODES.map((mode) => (
            <Tooltip key={mode.value}>
              <TooltipTrigger
                render={
                  <button
                    type="button"
                    disabled={!mode.available}
                    className={cn(
                      "flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-colors",
                      mode.available
                        ? "border-primary/30 bg-primary/10 text-primary"
                        : "cursor-not-allowed border-transparent text-muted-foreground/50"
                    )}
                  >
                    <mode.icon className="size-3.5" />
                    {mode.label}
                  </button>
                }
              />
              <TooltipContent>
                {mode.available ? "Searches the live web" : "Requires uploaded documents — coming soon"}
              </TooltipContent>
            </Tooltip>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <span className="hidden text-xs text-muted-foreground sm:inline">
            <Sparkles className="mr-1 inline size-3 align-[-1px]" />
            Auto
          </span>
          <span className="text-xs tabular-nums text-muted-foreground/70">
            {value.length}/{maxLength}
          </span>
          <Button
            type="button"
            size="icon-sm"
            onClick={onSubmit}
            disabled={!canSubmit}
            aria-label="Send"
          >
            {isSubmitting ? <Loader2 className="animate-spin" /> : <ArrowUp />}
          </Button>
        </div>
      </div>
    </div>
  );
}

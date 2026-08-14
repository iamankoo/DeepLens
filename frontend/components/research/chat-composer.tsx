"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useDropzone } from "react-dropzone";
import { ArrowUp, Globe, Layers, Loader2, Mic, MicOff, Paperclip, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { FileAttachmentList } from "@/components/research/file-attachment-list";
import { useFileAttachments } from "@/hooks/use-file-attachments";
import { cn } from "@/lib/utils";

interface SpeechRecognitionResultLike {
  0: { transcript: string };
}
interface SpeechRecognitionEventLike {
  results: ArrayLike<SpeechRecognitionResultLike>;
}
interface SpeechRecognitionLike {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
}

function getSpeechRecognitionCtor(): (new () => SpeechRecognitionLike) | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as {
    SpeechRecognition?: new () => SpeechRecognitionLike;
    webkitSpeechRecognition?: new () => SpeechRecognitionLike;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

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
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(false);

  useEffect(() => {
    setVoiceSupported(getSpeechRecognitionCtor() !== null);
    return () => {
      recognitionRef.current?.stop();
    };
  }, []);

  const onDrop = useCallback((accepted: File[]) => addFiles(accepted), [addFiles]);
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    noClick: true,
    noKeyboard: true,
  });

  const toggleVoiceInput = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      return;
    }

    const SpeechRecognitionCtor = getSpeechRecognitionCtor();
    if (!SpeechRecognitionCtor) {
      toast.error("Voice input isn't supported in this browser — try Chrome or Edge.");
      return;
    }

    const recognition = new SpeechRecognitionCtor();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0].transcript)
        .join(" ")
        .trim();
      if (transcript) {
        onChange(`${value ? `${value} ` : ""}${transcript}`.slice(0, maxLength));
      }
    };
    recognition.onerror = () => {
      toast.error("Couldn't capture audio — check microphone permissions.");
      setIsListening(false);
    };
    recognition.onend = () => setIsListening(false);

    recognitionRef.current = recognition;
    recognition.start();
    setIsListening(true);
  };

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
                      "flex items-center gap-1.5 rounded-full border px-2 py-1 text-xs font-medium transition-colors sm:px-2.5",
                      mode.available
                        ? "border-primary/30 bg-primary/10 text-primary"
                        : "cursor-not-allowed border-transparent text-muted-foreground/50"
                    )}
                  >
                    <mode.icon className="size-3.5" />
                    <span className="hidden sm:inline">{mode.label}</span>
                  </button>
                }
              />
              <TooltipContent>
                {mode.available ? "Searches the live web" : "Requires uploaded documents — coming soon"}
              </TooltipContent>
            </Tooltip>
          ))}

          <div className="mx-1 h-4 w-px bg-border" />

          <Tooltip>
            <TooltipTrigger
              render={
                <Button
                  type="button"
                  variant={isListening ? "default" : "ghost"}
                  size="icon-sm"
                  onClick={toggleVoiceInput}
                  disabled={isSubmitting}
                  className={cn(isListening && "animate-pulse")}
                  aria-label={isListening ? "Stop voice input" : "Start voice input"}
                >
                  {isListening ? <MicOff /> : <Mic />}
                </Button>
              }
            />
            <TooltipContent>
              {voiceSupported
                ? isListening
                  ? "Stop recording"
                  : "Dictate your research query"
                : "Voice input isn't supported in this browser"}
            </TooltipContent>
          </Tooltip>
        </div>

        <div className="flex items-center gap-2">
          <span className="hidden text-xs text-muted-foreground sm:inline">
            <Sparkles className="mr-1 inline size-3 align-[-1px]" />
            Auto
          </span>
          <span className="hidden text-xs tabular-nums text-muted-foreground/70 sm:inline">
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

"use client";

import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { formatFileSize, iconForFile } from "@/lib/file-types";
import type { AttachedFile } from "@/hooks/use-file-attachments";

export function FileAttachmentList({
  files,
  onRemove,
}: {
  files: AttachedFile[];
  onRemove: (id: string) => void;
}) {
  if (!files.length) return null;

  return (
    <div className="flex flex-wrap gap-2 px-3 pt-3">
      <AnimatePresence initial={false}>
        {files.map(({ id, file }) => {
          const Icon = iconForFile(file.name);
          return (
            <motion.div
              key={id}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.15 }}
              className="group flex items-center gap-2 rounded-lg border bg-muted/40 py-1.5 pr-1.5 pl-2 text-xs"
            >
              <Icon className="size-4 shrink-0 text-muted-foreground" />
              <div className="flex min-w-0 flex-col">
                <span className="max-w-40 truncate font-medium">{file.name}</span>
                <span className="text-[10px] text-muted-foreground">{formatFileSize(file.size)}</span>
              </div>
              <Badge variant="outline" className="text-[9px] text-muted-foreground">
                Soon
              </Badge>
              <button
                type="button"
                onClick={() => onRemove(id)}
                className="ml-0.5 flex size-5 shrink-0 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
                aria-label={`Remove ${file.name}`}
              >
                <X className="size-3.5" />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}

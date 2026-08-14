"use client";

import { useCallback, useState } from "react";
import { toast } from "sonner";

import { ACCEPTED_EXTENSIONS, MAX_FILES, MAX_FILE_SIZE_BYTES, isAcceptedFile } from "@/lib/file-types";

export interface AttachedFile {
  id: string;
  file: File;
}

// Document upload has no backend yet (Phase 5) — this manages real,
// interactive local file state (add/remove/validate) so the composer UI is
// fully built and ready, without pretending files are uploaded anywhere.
export function useFileAttachments() {
  const [files, setFiles] = useState<AttachedFile[]>([]);

  const addFiles = useCallback((incoming: FileList | File[]) => {
    setFiles((current) => {
      const next = [...current];
      for (const file of Array.from(incoming)) {
        if (next.length >= MAX_FILES) {
          toast.error(`You can attach up to ${MAX_FILES} files.`);
          break;
        }
        if (!isAcceptedFile(file.name)) {
          toast.error(`${file.name}: unsupported file type.`);
          continue;
        }
        if (file.size > MAX_FILE_SIZE_BYTES) {
          toast.error(`${file.name}: exceeds the 25 MB limit.`);
          continue;
        }
        next.push({ id: `${file.name}-${file.size}-${file.lastModified}`, file });
      }
      return next;
    });
  }, []);

  const removeFile = useCallback((id: string) => {
    setFiles((current) => current.filter((f) => f.id !== id));
  }, []);

  const clearFiles = useCallback(() => setFiles([]), []);

  return { files, addFiles, removeFile, clearFiles, acceptedExtensions: ACCEPTED_EXTENSIONS };
}

import {
  FileArchive,
  FileCode2,
  FileImage,
  FileSpreadsheet,
  FileText,
  type LucideIcon,
} from "lucide-react";

export const ACCEPTED_EXTENSIONS = [
  ".pdf",
  ".docx",
  ".txt",
  ".md",
  ".csv",
  ".xlsx",
  ".pptx",
  ".json",
  ".xml",
  ".html",
  ".png",
  ".jpg",
  ".jpeg",
  ".webp",
] as const;

export const MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024;
export const MAX_FILES = 10;

export function iconForFile(fileName: string): LucideIcon {
  const ext = fileName.toLowerCase().split(".").pop() ?? "";
  if (["png", "jpg", "jpeg", "webp"].includes(ext)) return FileImage;
  if (["csv", "xlsx"].includes(ext)) return FileSpreadsheet;
  if (["json", "xml", "html"].includes(ext)) return FileCode2;
  if (["pdf", "docx", "txt", "md", "pptx"].includes(ext)) return FileText;
  return FileArchive;
}

export function isAcceptedFile(fileName: string): boolean {
  const lower = fileName.toLowerCase();
  return ACCEPTED_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

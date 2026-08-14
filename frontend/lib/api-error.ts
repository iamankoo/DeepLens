import { isAxiosError } from "axios";

import type { ApiErrorBody } from "@/types/auth";

interface ValidationErrorItem {
  loc?: (string | number)[];
  msg?: string;
}

/**
 * Backend error bodies are inconsistent by design across two error paths:
 * FastAPI's own `HTTPException`/422 validation responses use `{ detail }`
 * (string, or an array of per-field errors), while the app's typed
 * exception handlers in `main.py` use `{ error, detail }` with `detail`
 * always a string. This normalizes both into one user-facing message.
 */
export function getApiErrorMessage(
  error: unknown,
  fallback = "Something went wrong. Please try again."
): string {
  if (!isAxiosError<ApiErrorBody | { detail?: ValidationErrorItem[] }>(error)) {
    return fallback;
  }

  const detail = error.response?.data?.detail;

  if (typeof detail === "string" && detail.length > 0) {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    const field = first.loc?.[first.loc.length - 1];
    return field ? `${field}: ${first.msg}` : first.msg ?? fallback;
  }

  if (error.code === "ERR_NETWORK") {
    return "Can't reach the server. Check your connection and try again.";
  }

  return fallback;
}

"use client";

import { useSearchParams } from "next/navigation";

import { ResetPasswordForm } from "@/components/auth/reset-password-form";

export function ResetPasswordFormWithParams() {
  const searchParams = useSearchParams();
  return <ResetPasswordForm token={searchParams.get("token")} />;
}

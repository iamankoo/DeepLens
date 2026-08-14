"use client";

import { useSearchParams } from "next/navigation";

import { VerifyEmailView } from "@/components/auth/verify-email-view";

export function VerifyEmailViewWithParams() {
  const searchParams = useSearchParams();
  return <VerifyEmailView token={searchParams.get("token")} />;
}

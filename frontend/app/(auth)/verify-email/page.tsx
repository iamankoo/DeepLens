import type { Metadata } from "next";
import { Suspense } from "react";

import { AuthShell } from "@/components/auth/auth-shell";
import { VerifyEmailViewWithParams } from "./verify-email-view-with-params";

export const metadata: Metadata = { title: "Verify email" };

export default function VerifyEmailPage() {
  return (
    <AuthShell title="Verify your email" description="One more step before you can sign in.">
      <Suspense fallback={null}>
        <VerifyEmailViewWithParams />
      </Suspense>
    </AuthShell>
  );
}

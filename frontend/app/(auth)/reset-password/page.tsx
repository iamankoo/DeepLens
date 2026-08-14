import type { Metadata } from "next";
import { Suspense } from "react";

import { AuthShell } from "@/components/auth/auth-shell";
import { ResetPasswordFormWithParams } from "./reset-password-form-with-params";

export const metadata: Metadata = { title: "Reset password" };

export default function ResetPasswordPage() {
  return (
    <AuthShell title="Set a new password" description="Choose a new password for your account.">
      <Suspense fallback={null}>
        <ResetPasswordFormWithParams />
      </Suspense>
    </AuthShell>
  );
}

"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm } from "react-hook-form";
import { CheckCircle2, Loader2, MailQuestion, ShieldAlert } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { useResendVerification, useVerifyEmail } from "@/hooks/use-auth";
import { forgotPasswordSchema, type ForgotPasswordFormValues } from "@/lib/validations/auth";

export function VerifyEmailView({ token }: { token: string | null }) {
  const verifyEmail = useVerifyEmail();
  const resendVerification = useResendVerification();
  const attempted = useRef(false);

  useEffect(() => {
    if (token && !attempted.current) {
      attempted.current = true;
      verifyEmail.mutate({ token });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const form = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: { email: "" },
  });

  if (token && verifyEmail.isPending) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-lg border bg-muted/40 p-6 text-center">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
        <p className="text-sm text-muted-foreground">Verifying your email address…</p>
      </div>
    );
  }

  if (token && verifyEmail.isSuccess) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-lg border bg-muted/40 p-6 text-center">
        <CheckCircle2 className="size-8 text-success" />
        <p className="text-sm text-foreground">Your email has been verified.</p>
        <Button size="sm" render={<Link href="/login" />}>
          Continue to sign in
        </Button>
      </div>
    );
  }

  if (resendVerification.isSuccess) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-lg border bg-muted/40 p-6 text-center">
        <CheckCircle2 className="size-8 text-success" />
        <p className="text-sm text-foreground">
          If an account exists for <span className="font-medium">{form.getValues("email")}</span>, a new
          verification link is on its way.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {token && verifyEmail.isError && (
        <div className="flex items-start gap-2.5 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          <ShieldAlert className="mt-0.5 size-4 shrink-0" />
          This link is invalid or has expired. Request a new one below.
        </div>
      )}
      {!token && (
        <div className="flex items-start gap-2.5 rounded-lg border bg-muted/40 p-3 text-sm text-muted-foreground">
          <MailQuestion className="mt-0.5 size-4 shrink-0" />
          Enter your email and we&apos;ll send a fresh verification link.
        </div>
      )}

      <form
        onSubmit={form.handleSubmit((values) => resendVerification.mutate(values))}
        noValidate
      >
        <FieldGroup>
          <Controller
            name="email"
            control={form.control}
            render={({ field, fieldState }) => (
              <Field data-invalid={fieldState.invalid}>
                <FieldLabel htmlFor={field.name}>Email</FieldLabel>
                <Input
                  {...field}
                  id={field.name}
                  type="email"
                  autoComplete="email"
                  placeholder="you@company.com"
                  aria-invalid={fieldState.invalid}
                />
                <FieldError errors={[fieldState.error]} />
              </Field>
            )}
          />

          <Button type="submit" size="lg" className="w-full" disabled={resendVerification.isPending}>
            {resendVerification.isPending && <Loader2 className="size-4 animate-spin" />}
            Resend verification email
          </Button>
        </FieldGroup>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        <Link href="/login" className="font-medium text-foreground underline-offset-4 hover:underline">
          Back to sign in
        </Link>
      </p>
    </div>
  );
}

"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm } from "react-hook-form";
import Link from "next/link";
import { Loader2, ShieldAlert } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { useResetPassword } from "@/hooks/use-auth";
import { resetPasswordSchema, type ResetPasswordFormValues } from "@/lib/validations/auth";

export function ResetPasswordForm({ token }: { token: string | null }) {
  const resetPassword = useResetPassword();
  const form = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: { password: "", confirmPassword: "" },
  });

  if (!token) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-lg border bg-muted/40 p-6 text-center">
        <ShieldAlert className="size-8 text-destructive" />
        <p className="text-sm text-foreground">This reset link is missing its token and can&apos;t be used.</p>
        <Link href="/forgot-password" className="text-sm font-medium underline-offset-4 hover:underline">
          Request a new link
        </Link>
      </div>
    );
  }

  return (
    <form
      onSubmit={form.handleSubmit((values) => resetPassword.mutate({ token, new_password: values.password }))}
      noValidate
    >
      <FieldGroup>
        <Controller
          name="password"
          control={form.control}
          render={({ field, fieldState }) => (
            <Field data-invalid={fieldState.invalid}>
              <FieldLabel htmlFor={field.name}>New password</FieldLabel>
              <Input
                {...field}
                id={field.name}
                type="password"
                autoComplete="new-password"
                placeholder="••••••••"
                aria-invalid={fieldState.invalid}
              />
              <FieldError errors={[fieldState.error]} />
            </Field>
          )}
        />

        <Controller
          name="confirmPassword"
          control={form.control}
          render={({ field, fieldState }) => (
            <Field data-invalid={fieldState.invalid}>
              <FieldLabel htmlFor={field.name}>Confirm new password</FieldLabel>
              <Input
                {...field}
                id={field.name}
                type="password"
                autoComplete="new-password"
                placeholder="••••••••"
                aria-invalid={fieldState.invalid}
              />
              <FieldError errors={[fieldState.error]} />
            </Field>
          )}
        />

        <Button type="submit" size="lg" className="w-full" disabled={resetPassword.isPending}>
          {resetPassword.isPending && <Loader2 className="size-4 animate-spin" />}
          Reset password
        </Button>
      </FieldGroup>
    </form>
  );
}

"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm } from "react-hook-form";
import Link from "next/link";
import { CheckCircle2, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { useForgotPassword } from "@/hooks/use-auth";
import { forgotPasswordSchema, type ForgotPasswordFormValues } from "@/lib/validations/auth";

export function ForgotPasswordForm() {
  const forgotPassword = useForgotPassword();
  const form = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: { email: "" },
  });

  if (forgotPassword.isSuccess) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-lg border bg-muted/40 p-6 text-center">
        <CheckCircle2 className="size-8 text-success" />
        <p className="text-sm text-foreground">
          If an account exists for <span className="font-medium">{form.getValues("email")}</span>, a reset link is
          on its way.
        </p>
        <Link href="/login" className="text-sm font-medium underline-offset-4 hover:underline">
          Back to sign in
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={form.handleSubmit((values) => forgotPassword.mutate(values))} noValidate>
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

        <Button type="submit" size="lg" className="w-full" disabled={forgotPassword.isPending}>
          {forgotPassword.isPending && <Loader2 className="size-4 animate-spin" />}
          Send reset link
        </Button>
      </FieldGroup>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        Remembered it?{" "}
        <Link href="/login" className="font-medium text-foreground underline-offset-4 hover:underline">
          Back to sign in
        </Link>
      </p>
    </form>
  );
}

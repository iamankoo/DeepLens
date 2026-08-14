import type { Metadata } from "next";

import { AuthCard } from "@/components/auth/auth-card";

export const metadata: Metadata = { title: "Create account" };

export default function RegisterPage() {
  return <AuthCard defaultTab="signup" />;
}

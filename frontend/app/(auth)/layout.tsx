"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuthStore } from "@/stores/auth-store";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const isHydrated = useAuthStore((state) => state.isHydrated);
  const accessToken = useAuthStore((state) => state.accessToken);

  useEffect(() => {
    if (isHydrated && accessToken) {
      router.replace("/dashboard");
    }
  }, [isHydrated, accessToken, router]);

  return <>{children}</>;
}

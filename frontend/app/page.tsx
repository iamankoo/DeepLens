"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuthStore } from "@/stores/auth-store";

export default function Home() {
  const router = useRouter();
  const isHydrated = useAuthStore((state) => state.isHydrated);
  const accessToken = useAuthStore((state) => state.accessToken);

  useEffect(() => {
    if (!isHydrated) return;
    router.replace(accessToken ? "/dashboard" : "/login");
  }, [isHydrated, accessToken, router]);

  return null;
}

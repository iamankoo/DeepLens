"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

import { useCurrentUser } from "@/hooks/use-auth";
import { useAuthStore } from "@/stores/auth-store";
import type { UserRole } from "@/types/auth";

function FullScreenLoader() {
  return (
    <div className="flex min-h-svh items-center justify-center">
      <Loader2 className="size-6 animate-spin text-muted-foreground" />
    </div>
  );
}

/**
 * Tokens live in localStorage via zustand/persist, which Next's edge
 * middleware can't read — so the guard runs client-side: wait for the
 * persisted store to hydrate, then require a token and a verified
 * `/auth/me` response before rendering protected children.
 */
export function RequireAuth({
  children,
  allowedRoles,
}: {
  children: React.ReactNode;
  allowedRoles?: UserRole[];
}) {
  const router = useRouter();
  const isHydrated = useAuthStore((state) => state.isHydrated);
  const accessToken = useAuthStore((state) => state.accessToken);
  const { data: user, isLoading, isError } = useCurrentUser();

  useEffect(() => {
    if (!isHydrated) return;
    if (!accessToken || isError) {
      router.replace("/login");
    }
  }, [isHydrated, accessToken, isError, router]);

  useEffect(() => {
    if (user && allowedRoles && !allowedRoles.includes(user.role)) {
      router.replace("/dashboard");
    }
  }, [user, allowedRoles, router]);

  if (!isHydrated || !accessToken || isLoading || !user) {
    return <FullScreenLoader />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <FullScreenLoader />;
  }

  return <>{children}</>;
}

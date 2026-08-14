"use client";

import { Loader2, LogOut, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useCurrentUser, useLogout } from "@/hooks/use-auth";

// Placeholder landing surface for the protected app shell — Phase 4c replaces
// this with the full sidebar/topnav layout; this page exists now to prove
// the auth guard + session flow work end-to-end.
export default function DashboardPage() {
  const { data: user } = useCurrentUser();
  const logout = useLogout();

  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-6 p-6 text-center">
      <span className="flex size-12 items-center justify-center rounded-xl bg-primary text-primary-foreground">
        <Sparkles className="size-6" />
      </span>
      <div className="space-y-1">
        <h1 className="text-xl font-semibold">You&apos;re signed in</h1>
        <p className="text-sm text-muted-foreground">
          {user?.email} · <span className="capitalize">{user?.role}</span>
        </p>
      </div>
      <Button
        variant="outline"
        onClick={() => logout.mutate()}
        disabled={logout.isPending}
      >
        {logout.isPending ? <Loader2 className="size-4 animate-spin" /> : <LogOut className="size-4" />}
        Sign out
      </Button>
    </div>
  );
}

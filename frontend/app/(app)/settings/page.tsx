"use client";

import { useTheme } from "next-themes";
import { CheckCircle2, Laptop, LogOut, Moon, ShieldAlert, Sun } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { SiteHeader } from "@/components/layout/site-header";
import { useCurrentUser, useLogout } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";

const THEME_OPTIONS = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "system", label: "System", icon: Laptop },
] as const;

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-3 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

export default function SettingsPage() {
  const { data: user, isLoading } = useCurrentUser();
  const { theme, setTheme } = useTheme();
  const logout = useLogout();

  return (
    <>
      <SiteHeader title="Settings" />

      <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 p-4 md:p-6">
        <Card>
          <CardHeader>
            <CardTitle>Account</CardTitle>
            <CardDescription>Your DeepLens account details.</CardDescription>
          </CardHeader>
          <CardContent className="divide-y">
            {isLoading || !user ? (
              <div className="space-y-3 py-2">
                <Skeleton className="h-5 w-full" />
                <Skeleton className="h-5 w-full" />
                <Skeleton className="h-5 w-full" />
              </div>
            ) : (
              <>
                <Row label="Email" value={user.email} />
                <Row label="Role" value={<span className="capitalize">{user.role}</span>} />
                <Row
                  label="Email verification"
                  value={
                    user.email_verified ? (
                      <Badge variant="outline" className="border-transparent bg-success/15 text-success">
                        <CheckCircle2 className="size-3" />
                        Verified
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="border-transparent bg-warning/15 text-warning">
                        <ShieldAlert className="size-3" />
                        Unverified
                      </Badge>
                    )
                  }
                />
                <Row label="Member since" value={new Date(user.created_at).toLocaleDateString()} />
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Appearance</CardTitle>
            <CardDescription>Choose how DeepLens looks on this device.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-3">
              {THEME_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setTheme(option.value)}
                  className={cn(
                    "flex flex-col items-center gap-2 rounded-lg border p-4 text-sm transition-colors hover:border-ring/50",
                    theme === option.value ? "border-primary bg-primary/5 text-foreground" : "text-muted-foreground"
                  )}
                >
                  <option.icon className="size-5" />
                  {option.label}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="border-destructive/30">
          <CardHeader>
            <CardTitle className="text-destructive">Session</CardTitle>
            <CardDescription>Sign out of DeepLens on this device.</CardDescription>
          </CardHeader>
          <CardContent>
            <Separator className="mb-4" />
            <Button variant="destructive" onClick={() => logout.mutate()} disabled={logout.isPending}>
              <LogOut />
              Sign out
            </Button>
          </CardContent>
        </Card>
      </div>
    </>
  );
}

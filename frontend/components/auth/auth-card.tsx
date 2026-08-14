"use client";

import { motion } from "framer-motion";
import { useRouter } from "next/navigation";

import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LoginForm } from "@/components/auth/login-form";
import { RegisterForm } from "@/components/auth/register-form";

export function AuthCard({ defaultTab }: { defaultTab: "login" | "signup" }) {
  const router = useRouter();

  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-8 px-4 py-12 sm:gap-10 sm:px-6">
      <motion.div
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="text-center"
      >
        <h1 className="font-heading text-[clamp(3.5rem,18vw,18rem)] leading-none font-bold tracking-tight text-foreground">
          DeepLens
        </h1>
        <p className="mt-4 text-sm text-muted-foreground sm:text-base">
          Deep research, done properly — planned, verified, and cited.
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1, ease: "easeOut" }}
        className="w-full max-w-md"
      >
        <Card className="ring-foreground/10">
          <CardContent className="pt-2 pb-1">
            <Tabs
              value={defaultTab}
              onValueChange={(value) => {
                if (value === defaultTab) return;
                router.push(value === "login" ? "/login" : "/register");
              }}
            >
              <TabsList className="mb-6 grid h-10 w-full grid-cols-2">
                <TabsTrigger value="login" className="text-sm">
                  Login
                </TabsTrigger>
                <TabsTrigger value="signup" className="text-sm">
                  Signup
                </TabsTrigger>
              </TabsList>
              <TabsContent value="login">
                <LoginForm />
              </TabsContent>
              <TabsContent value="signup">
                <RegisterForm />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}

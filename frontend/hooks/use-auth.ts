"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { authService } from "@/services/auth-service";
import { useAuthStore } from "@/stores/auth-store";
import { getApiErrorMessage } from "@/lib/api-error";
import type {
  ForgotPasswordPayload,
  LoginPayload,
  RegisterPayload,
  ResendVerificationPayload,
  ResetPasswordPayload,
  VerifyEmailPayload,
} from "@/types/auth";

export const CURRENT_USER_QUERY_KEY = ["auth", "me"] as const;

/** Fetches the authenticated user; disabled until the persisted store has hydrated and a token exists. */
export function useCurrentUser() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const isHydrated = useAuthStore((state) => state.isHydrated);
  const setUser = useAuthStore((state) => state.setUser);
  const clearAuth = useAuthStore((state) => state.clearAuth);

  return useQuery({
    queryKey: CURRENT_USER_QUERY_KEY,
    queryFn: async () => {
      try {
        const user = await authService.me();
        setUser(user);
        return user;
      } catch (error) {
        clearAuth();
        throw error;
      }
    },
    enabled: isHydrated && !!accessToken,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });
}

export function useLogin() {
  const router = useRouter();
  const setTokens = useAuthStore((state) => state.setTokens);
  const setUser = useAuthStore((state) => state.setUser);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: LoginPayload) => authService.login(payload),
    onSuccess: async (tokens) => {
      setTokens({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
      const user = await authService.me();
      setUser(user);
      queryClient.setQueryData(CURRENT_USER_QUERY_KEY, user);
      toast.success(`Welcome back, ${user.email}`);
      router.push("/dashboard");
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Incorrect email or password"));
    },
  });
}

export function useRegister() {
  const router = useRouter();

  return useMutation({
    mutationFn: (payload: RegisterPayload) => authService.register(payload),
    onSuccess: () => {
      toast.success("Account created. Check your email to verify your address.");
      router.push("/login");
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Could not create account"));
    },
  });
}

export function useLogout() {
  const router = useRouter();
  const clearAuth = useAuthStore((state) => state.clearAuth);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const refreshToken = useAuthStore.getState().refreshToken;
      if (refreshToken) {
        await authService.logout(refreshToken);
      }
    },
    onSettled: () => {
      clearAuth();
      queryClient.removeQueries({ queryKey: CURRENT_USER_QUERY_KEY });
      router.push("/login");
    },
  });
}

export function useForgotPassword() {
  return useMutation({
    mutationFn: (payload: ForgotPasswordPayload) => authService.forgotPassword(payload),
    onSuccess: (data) => toast.success(data.message),
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

export function useResetPassword() {
  const router = useRouter();

  return useMutation({
    mutationFn: (payload: ResetPasswordPayload) => authService.resetPassword(payload),
    onSuccess: (data) => {
      toast.success(data.message);
      router.push("/login");
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Reset link is invalid or has expired"));
    },
  });
}

export function useVerifyEmail() {
  return useMutation({
    mutationFn: (payload: VerifyEmailPayload) => authService.verifyEmail(payload),
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Verification link is invalid or has expired"));
    },
  });
}

export function useResendVerification() {
  return useMutation({
    mutationFn: (payload: ResendVerificationPayload) => authService.resendVerification(payload),
    onSuccess: (data) => toast.success(data.message),
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });
}

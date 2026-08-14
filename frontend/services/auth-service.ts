import { apiClient } from "@/lib/api-client";
import type {
  ForgotPasswordPayload,
  LoginPayload,
  MessageResponse,
  RegisterPayload,
  ResendVerificationPayload,
  ResetPasswordPayload,
  TokenPair,
  UserPublic,
  VerifyEmailPayload,
} from "@/types/auth";

export const authService = {
  async register(payload: RegisterPayload): Promise<UserPublic> {
    const { data } = await apiClient.post<UserPublic>("/auth/register", payload);
    return data;
  },

  async login(payload: LoginPayload): Promise<TokenPair> {
    const { data } = await apiClient.post<TokenPair>("/auth/login", payload);
    return data;
  },

  async me(): Promise<UserPublic> {
    const { data } = await apiClient.get<UserPublic>("/auth/me");
    return data;
  },

  async logout(refreshToken: string): Promise<void> {
    await apiClient.post("/auth/logout", { refresh_token: refreshToken });
  },

  async forgotPassword(payload: ForgotPasswordPayload): Promise<MessageResponse> {
    const { data } = await apiClient.post<MessageResponse>("/auth/forgot-password", payload);
    return data;
  },

  async resetPassword(payload: ResetPasswordPayload): Promise<MessageResponse> {
    const { data } = await apiClient.post<MessageResponse>("/auth/reset-password", payload);
    return data;
  },

  async verifyEmail(payload: VerifyEmailPayload): Promise<MessageResponse> {
    const { data } = await apiClient.post<MessageResponse>("/auth/verify-email", payload);
    return data;
  },

  async resendVerification(payload: ResendVerificationPayload): Promise<MessageResponse> {
    const { data } = await apiClient.post<MessageResponse>("/auth/resend-verification", payload);
    return data;
  },
};

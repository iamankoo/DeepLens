import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { UserPublic } from "@/types/auth";

interface AuthState {
  user: UserPublic | null;
  accessToken: string | null;
  refreshToken: string | null;
  isHydrated: boolean;
  setUser: (user: UserPublic) => void;
  setTokens: (params: { accessToken: string; refreshToken: string }) => void;
  clearAuth: () => void;
  setHydrated: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isHydrated: false,
      setUser: (user) => set({ user }),
      setTokens: ({ accessToken, refreshToken }) =>
        set({ accessToken, refreshToken }),
      clearAuth: () => set({ user: null, accessToken: null, refreshToken: null }),
      setHydrated: () => set({ isHydrated: true }),
    }),
    {
      name: "deeplens-auth",
      onRehydrateStorage: () => (state) => {
        state?.setHydrated();
      },
    }
  )
);

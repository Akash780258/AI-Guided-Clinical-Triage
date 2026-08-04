import { create } from "zustand";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;

  setTokens: (
    access: string,
    refresh: string
  ) => void;

  logout: () => void;
}

export const useAuthStore =
  create<AuthState>((set) => ({
    accessToken: null,
    refreshToken: null,

    setTokens: (access, refresh) => {
      localStorage.setItem(
        "accessToken",
        access
      );

      localStorage.setItem(
        "refreshToken",
        refresh
      );

      set({
        accessToken: access,
        refreshToken: refresh,
      });
    },

    logout: () => {
      localStorage.clear();

      set({
        accessToken: null,
        refreshToken: null,
      });
    },
  }));
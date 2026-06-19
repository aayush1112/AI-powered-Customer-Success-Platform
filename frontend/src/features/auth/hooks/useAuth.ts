"use client";

import { useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAppDispatch } from "@/hooks/useAppDispatch";
import { useAppSelector } from "@/hooks/useAppSelector";
import { setCredentials, clearCredentials } from "@/store/slices/authSlice";
import { tokenStorage } from "@/lib/tokenStorage";
import {
  useLoginMutation,
  useLogoutMutation,
  useRegisterMutation,
} from "@/services/api/authApi";
import type { LoginRequest, RegisterRequest, UserResponse } from "../types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function useAuth() {
  const dispatch = useAppDispatch();
  const router = useRouter();

  const { user, isAuthenticated, accessToken, isLoading, isInitialized, error } =
    useAppSelector((s) => s.auth);

  const [loginMutation, { isLoading: isLoginLoading }] = useLoginMutation();
  const [logoutMutation, { isLoading: isLogoutLoading }] = useLogoutMutation();
  const [registerMutation, { isLoading: isRegisterLoading }] = useRegisterMutation();

  const login = useCallback(
    async (data: LoginRequest): Promise<UserResponse> => {
      const tokens = await loginMutation(data).unwrap();

      // Refresh token is now handled via httpOnly cookie
      tokenStorage.saveTokens();

      // Fetch profile with the new access token
      const meRes = await fetch(`${API_BASE}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${tokens.access_token}` },
      });
      if (!meRes.ok) throw new Error("Failed to load user profile");
      const profile: UserResponse = await meRes.json();

      dispatch(setCredentials({ user: profile, accessToken: tokens.access_token }));
      return profile;
    },
    [dispatch, loginMutation]
  );

  const logout = useCallback(async (): Promise<void> => {
    try {
      await logoutMutation().unwrap();
    } finally {
      tokenStorage.clearTokens();
      dispatch(clearCredentials());
      router.push("/login");
    }
  }, [dispatch, logoutMutation, router]);

  const register = useCallback(
    async (data: RegisterRequest) => registerMutation(data).unwrap(),
    [registerMutation]
  );

  return {
    user,
    isAuthenticated,
    accessToken,
    isInitialized,
    error,
    isLoading: isLoading || isLoginLoading || isLogoutLoading || isRegisterLoading,
    login,
    logout,
    register,
  };
}

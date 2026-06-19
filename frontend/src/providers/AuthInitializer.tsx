"use client";

import { useEffect } from "react";
import { useAppDispatch } from "@/hooks/useAppDispatch";
import { setCredentials, setInitialized } from "@/store/slices/authSlice";
import { tokenStorage } from "@/lib/tokenStorage";
import type { UserResponse } from "@/features/auth/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Silently re-hydrates auth state on every page load.
 *
 * Flow:
 *  1. Read refresh_token from localStorage
 *  2. POST /auth/refresh → new access_token
 *  3. GET /auth/me → user profile
 *  4. Dispatch setCredentials → components become aware of the session
 *
 * If any step fails (expired token, network error, revoked) we clear storage
 * and mark auth as initialized so the app can redirect to /login if needed.
 *
 * This component renders nothing — it is mounted once inside <Providers>.
 */
export function AuthInitializer() {
  const dispatch = useAppDispatch();

  useEffect(() => {
    let cancelled = false;

    async function hydrate() {
      try {
        const refreshRes = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
          method: "POST",
          credentials: "include",
        });

        if (!refreshRes.ok) {
          tokenStorage.clearTokens();
          if (!cancelled) dispatch(setInitialized());
          return;
        }

        const { access_token } = (await refreshRes.json()) as {
          access_token: string;
        };

        const meRes = await fetch(`${API_BASE}/api/v1/auth/me`, {
          headers: { Authorization: `Bearer ${access_token}` },
        });

        if (!meRes.ok) {
          tokenStorage.clearTokens();
          if (!cancelled) dispatch(setInitialized());
          return;
        }

        const user: UserResponse = await meRes.json();
        if (!cancelled) {
          dispatch(setCredentials({ user, accessToken: access_token }));
        }
      } catch {
        tokenStorage.clearTokens();
        if (!cancelled) dispatch(setInitialized());
      }
    }

    hydrate();
    return () => {
      cancelled = true;
    };
  }, [dispatch]);

  return null;
}

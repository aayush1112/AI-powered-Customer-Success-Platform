/**
 * Token storage strategy:
 *
 * Access token  → Redux state (in-memory). Never persisted. Cleared on page
 *                 refresh; re-acquired via the refresh flow on next load.
 *
 * Refresh token → localStorage. Survives page refreshes and tab closes.
 *                 In-memory XSS risk is mitigated by: short access token TTL
 *                 (15 min), token rotation per request, CSP headers, and the
 *                 B2B/internal nature of this application.
 *
 * Middleware     → A non-httpOnly cookie called `auth_status` is set by JS
 *                 on login and cleared on logout. It carries no sensitive
 *                 data — it is only used by Next.js Edge middleware to decide
 *                 whether to redirect unauthenticated visits to /login.
 *
 * Production upgrade path:
 *   When deploying behind Nginx on a single domain, move to httpOnly cookies:
 *   1. Backend: Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Lax
 *   2. Frontend: Remove localStorage reads; rely solely on the cookie.
 *   3. Middleware: Change to checking the httpOnly cookie (works server-side).
 */

const AUTH_STATUS_COOKIE = "auth_status";

function _setCookie(name: string, value: string, days: number): void {
  if (typeof document === "undefined") return;
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${value}; expires=${expires}; path=/; SameSite=Lax`;
}

function _deleteCookie(name: string): void {
  if (typeof document === "undefined") return;
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
}

export const tokenStorage = {
  saveTokens(): void {
    if (typeof window === "undefined") return;
    _setCookie(AUTH_STATUS_COOKIE, "1", 7);
  },

  clearTokens(): void {
    _deleteCookie(AUTH_STATUS_COOKIE);
  },
};

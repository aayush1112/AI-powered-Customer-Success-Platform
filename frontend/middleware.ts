import { type NextRequest, NextResponse } from "next/server";

/**
 * Route protection strategy:
 *
 * The `auth_status` cookie is a non-sensitive, non-httpOnly flag set by
 * tokenStorage.ts when the user logs in and cleared on logout. It exists
 * solely so Edge middleware can make a redirect decision without requiring
 * access to localStorage (which is unavailable in the Edge runtime).
 *
 * This is a UX guard, not a security boundary — actual API security is
 * enforced by Bearer token validation on every FastAPI request.
 */

const PROTECTED = ["/dashboard", "/customers", "/interactions", "/admin"];
const AUTH_ROUTES = ["/login", "/register"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasSession = request.cookies.has("auth_status");

  // Redirect unauthenticated users away from protected routes
  if (PROTECTED.some((p) => pathname.startsWith(p)) && !hasSession) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("redirect", pathname);
    return NextResponse.redirect(url);
  }

  // Redirect already-authenticated users away from login/register
  if (AUTH_ROUTES.includes(pathname) && hasSession) {
    const url = request.nextUrl.clone();
    url.pathname = "/dashboard";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/customers/:path*",
    "/interactions/:path*",
    "/admin/:path*",
    "/login",
    "/register",
  ],
};

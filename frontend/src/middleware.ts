import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const STACK_AUTH_PATHS = [
  "/api/v1/auth/",
  "/api/v1/users/",
  "/api/v1/projects/",
  "/api/v1/internal/",
  "/api/v1/teams/",
  "/api/v1/analytics/",
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (STACK_AUTH_PATHS.some((p) => pathname.startsWith(p))) {
    const requestHeaders = new Headers(request.headers);

    if (!requestHeaders.has("x-hexclave-access-type")) {
      requestHeaders.set("x-hexclave-access-type", "client");
    }
    if (!requestHeaders.has("x-hexclave-publishable-client-key")) {
      requestHeaders.set("x-hexclave-publishable-client-key", "12345678");
    }
    if (!requestHeaders.has("x-hexclave-project-id")) {
      requestHeaders.set("x-hexclave-project-id", "internal");
    }

    return NextResponse.next({
      request: { headers: requestHeaders },
    });
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/api/v1/:path*"],
};

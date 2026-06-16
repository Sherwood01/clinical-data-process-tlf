import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",

  async rewrites() {
    // STACK_AUTH_REWRITE_URL defaults to Docker internal DNS; override for local dev (e.g. http://localhost:8102)
    const stackAuthUrl = process.env.STACK_AUTH_REWRITE_URL || "http://stack-auth:8102";
    return [
      {
        source: "/api/v1/auth/:path*",
        destination: `${stackAuthUrl}/api/v1/auth/:path*`,
      },
      {
        source: "/api/v1/users/:path*",
        destination: `${stackAuthUrl}/api/v1/users/:path*`,
      },
      {
        source: "/api/v1/projects/:path*",
        destination: `${stackAuthUrl}/api/v1/projects/:path*`,
      },
      {
        source: "/api/v1/internal/:path*",
        destination: `${stackAuthUrl}/api/v1/internal/:path*`,
      },
      {
        source: "/api/v1/teams/:path*",
        destination: `${stackAuthUrl}/api/v1/teams/:path*`,
      },
      {
        source: "/api/v1/analytics/:path*",
        destination: `${stackAuthUrl}/api/v1/analytics/:path*`,
      },
      // Application API — proxy to FastAPI backend
      // API_REWRITE_URL is a runtime env var, not NEXT_PUBLIC_*, so it's NOT inlined at build time.
      // Default: localhost for local dev, override with Docker internal URL when inside Docker.
      {
        source: "/api/v1/:path*",
        destination: `${process.env.API_REWRITE_URL || "http://localhost:8100/api/v1"}/:path*`,
      },
    ];
  },
};

export default nextConfig;

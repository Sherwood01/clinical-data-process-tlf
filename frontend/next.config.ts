import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",

  async rewrites() {
    return [
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

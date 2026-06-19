import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",

  async rewrites() {
    return [
      // Application API — proxy to FastAPI backend
      // 在 Docker 内部使用 service name (api:8000)，因为容器间在同一 network
      // 本地开发则通过 localhost:8100 直连
      {
        source: "/api/v1/:path*",
        destination: `${process.env.API_REWRITE_URL || "http://localhost:8100/api/v1"}/:path*`,
      },
    ];
  },
};

export default nextConfig;

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: [
    "192.168.31.194",
    "192.168.31.194:3100",
    "192.168.31.194:3000",
    "localhost:3100",
    "localhost:3000",
    "127.0.0.1:3100",
    "127.0.0.1:3000"
  ],
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

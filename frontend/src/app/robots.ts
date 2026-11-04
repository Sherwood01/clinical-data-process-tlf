import type { MetadataRoute } from "next";

/**
 * 站点默认基础 URL
 */
const DEFAULT_SITE_URL = "https://tlf.xwqin.com";

/**
 * 生产环境部署域名
 */
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || DEFAULT_SITE_URL;

/**
 * 生成 robots.txt 路由规则，明确告知网络爬虫和 AI Agent 抓取范围。
 *
 * @returns {MetadataRoute.Robots} Next.js 标准 Robots 配置对象
 */
export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: [
          "/",
          "/terms",
          "/privacy",
          "/llms.txt",
          "/llms-full.txt",
          "/ads.txt",
        ],
        disallow: [
          "/dashboard",
          "/dashboard/*",
          "/studies",
          "/studies/*",
          "/billing",
          "/billing/*",
          "/knowledge",
          "/knowledge/*",
          "/help",
          "/help/*",
          "/auth",
          "/auth/*",
          "/handler",
          "/handler/*",
          "/api",
          "/api/*",
        ],
      },
      {
        userAgent: [
          "GPTBot",
          "ChatGPT-User",
          "ClaudeBot",
          "PerplexityBot",
          "Google-Extended",
          "Applebot-Extended",
        ],
        allow: ["/", "/terms", "/privacy", "/llms.txt", "/llms-full.txt"],
        disallow: [
          "/dashboard/*",
          "/studies/*",
          "/billing/*",
          "/knowledge/*",
          "/help/*",
          "/auth/*",
          "/handler/*",
          "/api/*",
        ],
      },
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}


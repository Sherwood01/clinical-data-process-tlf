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
 * 营销与合规页面的基准更新时间戳
 */
const BASELINE_MODIFIED_DATE = new Date("2026-11-01T00:00:00.000Z");

/**
 * 首页爬虫权重
 */
const HOME_PRIORITY = 1.0;

/**
 * 条款与隐私等次要合规页面的爬虫权重
 */
const LEGAL_PAGE_PRIORITY = 0.3;

/**
 * 生成 sitemap.xml 网站地图，包含当前站点所有对外公开的索引页面。
 *
 * @returns {MetadataRoute.Sitemap} Next.js 标准 Sitemap 配置数组
 */
export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: `${SITE_URL}`,
      lastModified: BASELINE_MODIFIED_DATE,
      changeFrequency: "weekly",
      priority: HOME_PRIORITY,
    },
    {
      url: `${SITE_URL}/terms`,
      lastModified: BASELINE_MODIFIED_DATE,
      changeFrequency: "monthly",
      priority: LEGAL_PAGE_PRIORITY,
    },
    {
      url: `${SITE_URL}/privacy`,
      lastModified: BASELINE_MODIFIED_DATE,
      changeFrequency: "monthly",
      priority: LEGAL_PAGE_PRIORITY,
    },
  ];
}


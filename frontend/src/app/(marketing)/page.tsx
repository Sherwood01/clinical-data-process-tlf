import type { Metadata } from "next";
import { Suspense } from "react";
import { LandingPage } from "@/components/landing-page";

export const dynamic = "force-dynamic";

/**
 * 生产环境部署域名或默认域名
 */
const DEFAULT_SITE_URL = "https://tlf.xwqin.com";
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || DEFAULT_SITE_URL;

/**
 * 首页专用 SEO 元数据
 */
export const metadata: Metadata = {
  title: "TLF Report Generator | AI Clinical Trial Reporting & Validation",
  description:
    "Transform CDISC ADaM datasets and Statistical Analysis Plans (SAP) into publication-ready, 21 CFR Part 11 compliant clinical trial TLF reports in minutes.",
  alternates: {
    canonical: SITE_URL,
  },
};

/**
 * 结构化数据对象 (Schema.org JSON-LD)，增强在 Google 等搜索引擎中的富媒体摘要展示。
 */
const jsonLdData = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "SoftwareApplication",
      "name": "TLF Report Generator",
      "applicationCategory": "HealthApplication",
      "operatingSystem": "Web Browser",
      "url": SITE_URL,
      "description":
        "AI-powered clinical trial TLF report generation platform supporting CDISC ADaM validation, SAP document parsing, and automated SAS macro generation.",
      "offers": {
        "@type": "Offer",
        "price": "0",
        "priceCurrency": "USD",
      },
      "featureList": [
        "Automated SAP document parsing and TOC extraction",
        "CDISC ADaM dataset validation (SAS, XPT, CSV)",
        "Automated SAS macro matching and code generation",
        "ICH E3 compliant publication-ready PDF export",
        "21 CFR Part 11 validation audit trails",
      ],
    },
    {
      "@type": "Organization",
      "name": "TLF Report Generator",
      "url": SITE_URL,
      "logo": `${SITE_URL}/file.svg`,
    },
  ],
};

/**
 * 营销官网首页服务端组件。
 * 嵌入 JSON-LD 结构化数据，并通过 Suspense 加载客户端交互组件。
 *
 * @returns {React.ReactElement} 首页组件树
 */
export default function HomePage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLdData) }}
      />
      <Suspense
        fallback={
          <div className="flex min-h-screen items-center justify-center">
            <div className="text-gray-500">Loading...</div>
          </div>
        }
      >
        <LandingPage />
      </Suspense>
    </>
  );
}

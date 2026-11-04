import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/components/providers";

/**
 * 生产环境部署域名或默认域名
 */
const DEFAULT_SITE_URL = "https://tlf.xwqin.com";
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || DEFAULT_SITE_URL;

/**
 * 全局 SEO 基础元数据配置，适用于欧美临床数据处理与生物统计 SaaS 平台
 */
export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "TLF Report Generator | AI Clinical Trial Reporting & Validation",
    template: "%s | TLF Report Generator",
  },
  description:
    "AI-powered clinical trial TLF report generation platform. Automatically parse SAP documents, validate CDISC ADaM datasets, and generate regulatory-compliant SAS reports.",
  keywords: [
    "Clinical Trial TLF",
    "TLF Report Generator",
    "Biostatistics Automation",
    "CDISC ADaM Validation",
    "Statistical Analysis Plan",
    "SAP to TLF",
    "SAS Clinical Programming",
    "ICH E3 Compliance",
    "21 CFR Part 11 Audit Trail",
  ],
  authors: [{ name: "TLF Engineering Team", url: SITE_URL }],
  creator: "TLF Report Generator",
  publisher: "TLF Report Generator",
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  alternates: {
    canonical: SITE_URL,
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: SITE_URL,
    siteName: "TLF Report Generator",
    title: "TLF Report Generator | AI Clinical Trial Reporting & Validation",
    description:
      "Transform CDISC ADaM datasets and Statistical Analysis Plans (SAP) into publication-ready, 21 CFR Part 11 compliant clinical trial TLF reports.",
  },
  twitter: {
    card: "summary_large_image",
    title: "TLF Report Generator | AI Clinical Trial Reporting & Validation",
    description:
      "AI-powered clinical trial TLF report generation platform for biostatisticians and SAS programmers.",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
};

/**
 * 根布局组件，为整个应用注入语言标签、基础样式与状态管理 Provider。
 *
 * @param {Readonly<{ children: React.ReactNode }>} props 组件输入属性
 * @returns {React.ReactElement} 渲染的根 HTML 树
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased" suppressHydrationWarning>
      <head />
      <body className="min-h-full">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

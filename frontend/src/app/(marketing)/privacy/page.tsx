"use client";

import Link from "next/link";
import { ArrowLeft, ShieldCheck, Calendar, Lock } from "lucide-react";

/**
 * 隐私政策页面组件 (Privacy Policy)。
 * 渲染符合 Lemon Squeezy 商家合规性审核的英文隐私政策条款，使用精美现代的排版和 HSL 渐变卡片。
 */
export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-gray-50/50 dark:bg-gray-900/10 py-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        {/* 返回首页 */}
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900 dark:hover:text-white transition-colors mb-8 group"
        >
          <ArrowLeft className="h-4 w-4 group-hover:-translate-x-0.5 transition-transform" />
          Back to Homepage
        </Link>

        {/* 隐私政策主卡片 */}
        <div className="bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-3xl p-8 md:p-12 shadow-xl shadow-gray-100/40 dark:shadow-none relative overflow-hidden">
          {/* 背景彩光微点缀 */}
          <div className="absolute top-0 right-0 h-40 w-40 bg-emerald-500/5 rounded-full blur-3xl" />
          
          <div className="flex items-center gap-3 mb-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <span className="text-xs font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
              Privacy Declaration
            </span>
          </div>

          <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight">
            Privacy Policy
          </h1>

          <div className="flex items-center gap-1.5 text-xs text-gray-400 dark:text-gray-500 mt-3 mb-8">
            <Calendar className="h-3.5 w-3.5" />
            Last Updated: June 24, 2026
          </div>

          {/* 政策正文 */}
          <div className="prose prose-emerald dark:prose-invert max-w-none text-sm text-gray-600 dark:text-gray-400 space-y-6 leading-relaxed">
            <p>
              At TLF Report Generator, operated at{" "}
              <a href="https://tlf.xwqin.com" className="text-emerald-600 hover:underline">
                https://tlf.xwqin.com
              </a>
              , we prioritize protecting the privacy of our clinical research users and tenants. This document details the types of information we collect and how we safeguard it.
            </p>

            <h3 className="text-lg font-bold text-gray-900 dark:text-white pt-2">
              1. Information We Collect
            </h3>
            <ul className="list-disc pl-5 space-y-2">
              <li>
                <strong>Account Credentials:</strong> When you register, we collect personal registration data such as your name, email address, and authentication tokens handled securely via SuperTokens.
              </li>
              <li>
                <strong>Billing Metadata:</strong> Subscription payments are processed directly by our payment reseller, Lemon Squeezy. We do not store or process your credit card numbers on our local databases.
              </li>
              <li>
                <strong>Clinical Content:</strong> We temporarily store dataset files (e.g., SAS7BDAT, CSV), SAPs, and generated reports you upload or compile. These are isolated per tenant.
              </li>
            </ul>

            <h3 className="text-lg font-bold text-gray-900 dark:text-white pt-2">
              2. How We Use Your Information
            </h3>
            <p>
              We use the collected information strictly to:
              <br />
              - Provision and maintain your secure multi-tenant clinical workspace.
              <br />
              - Authenticate access logs and enforce role-based access controls.
              <br />
              - Handle webhook callbacks from Lemon Squeezy to keep subscription statuses updated.
              <br />
              - Perform system auditing and monitor service health.
            </p>

            <div className="bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200/50 dark:border-emerald-900/50 p-5 rounded-2xl my-6 flex gap-3 text-emerald-900 dark:text-emerald-300">
              <Lock className="h-5 w-5 flex-shrink-0 mt-0.5 text-emerald-600" />
              <div>
                <strong className="block text-sm mb-1 font-bold">3. Data Protection (HIPAA & GDPR Alignment)</strong>
                <p className="text-xs leading-relaxed">
                  We enforce technical and administrative safeguards: All data in transit is encrypted using TLS 1.3, and all data at rest is encrypted using AES-256. When you request the deletion of a dataset or Study, the corresponding storage objects are permanently deleted immediately.
                </p>
              </div>
            </div>

            <h3 className="text-lg font-bold text-gray-900 dark:text-white pt-2">
              4. Third-Party Integrations
            </h3>
            <p>
              We only share account or billing metadata with verified compliance partners:
              <br />
              - <strong>SuperTokens</strong> (for role-based authentication and secure session encryption)
              <br />
              - <strong>Creem</strong> (as our checkout and payment partner for handling invoices and secure processing)
            </p>

            <h3 className="text-lg font-bold text-gray-900 dark:text-white pt-2">
              5. Contact Us
            </h3>
            <p>
              If you have any questions regarding this Privacy Policy, please feel free to reach out to us at{" "}
              <a href="mailto:info@xwqin.com" className="text-emerald-600 hover:underline">
                info@xwqin.com
              </a>
              .
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

"use client";

import { Suspense } from "react";
import dynamic from "next/dynamic";

const BillingContent = dynamic(
  () => import("@/components/billing/billing-content"),
  { ssr: false }
);

export default function BillingPage() {
  return (
    <Suspense fallback={
      <div className="min-h-[80vh] flex flex-col items-center justify-center text-gray-500 dark:text-gray-400 gap-3">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        <p className="text-sm">正在加载计费与订阅面板...</p>
      </div>
    }>
      <BillingContent />
    </Suspense>
  );
}

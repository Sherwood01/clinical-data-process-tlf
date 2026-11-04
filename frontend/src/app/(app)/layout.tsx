"use client";

export const dynamic = "force-dynamic";

import { Suspense } from "react";
import { AppShell } from "@/components/app-shell";
import { BreadcrumbProvider } from "@/lib/breadcrumb-context";

function LoadingFallback() {
  return (
    <div className="flex h-screen items-center justify-center bg-background">
      <div className="text-muted-foreground">Loading...</div>
    </div>
  );
}

/**
 * 后台应用控制台布局组件。
 * 该布局覆盖所有内部业务路径，强制声明 noindex, nofollow 避免搜索引擎索引受保护的用户空间。
 *
 * @param {{ children: React.ReactNode }} props 组件输入属性
 * @returns {React.ReactElement} 后台壳层布局
 */
export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <head>
        <meta name="robots" content="noindex, nofollow" />
      </head>
      <Suspense fallback={<LoadingFallback />}>
        <BreadcrumbProvider>
          <AppShell>{children}</AppShell>
        </BreadcrumbProvider>
      </Suspense>
    </>
  );
}

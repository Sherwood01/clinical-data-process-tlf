import type { Metadata } from "next";
import { Suspense } from "react";
import { AppShell } from "@/components/app-shell";
import { BreadcrumbProvider } from "@/lib/breadcrumb-context";

export const dynamic = "force-dynamic";

/**
 * 内部受保护页面的元数据配置，阻止搜索引擎抓取用户私人工作空间。
 */
export const metadata: Metadata = {
  robots: {
    index: false,
    follow: false,
  },
};

/**
 * 页面加载占位降级组件。
 *
 * @returns {React.ReactElement} 居中全屏加载提示
 */
function LoadingFallback() {
  return (
    <div className="flex h-screen items-center justify-center bg-background">
      <div className="text-muted-foreground">Loading...</div>
    </div>
  );
}

/**
 * 后台应用控制台布局组件。
 * 该布局覆盖所有内部业务路径，包裹全局面包屑上下文与核心界面外壳（AppShell）。
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
    <Suspense fallback={<LoadingFallback />}>
      <BreadcrumbProvider>
        <AppShell>{children}</AppShell>
      </BreadcrumbProvider>
    </Suspense>
  );
}

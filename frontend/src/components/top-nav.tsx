"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { useSessionContext } from "supertokens-auth-react/recipe/session";
import { signOut } from "supertokens-auth-react/recipe/thirdparty";
import { ChevronRight, LogOut } from "lucide-react";
import { useUserEmail } from "@/lib/use-user-email";
import { useBreadcrumb } from "@/lib/breadcrumb-context";

function getBreadcrumbs(pathname: string, customLabels: Record<string, string>): { label: string; href: string }[] {
  const parts = pathname.split("/").filter(Boolean);
  const crumbs: { label: string; href: string }[] = [];
  let href = "";

  for (const part of parts) {
    href += "/" + part;
    if (part.startsWith("[")) continue;
    
    // 优先采用自定义的面包屑映射文字（如 Study 名称）
    const label = customLabels[part] || part
      .replace(/-/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
      
    crumbs.push({ label, href });
  }
  return crumbs;
}

/**
 * 顶部导航栏组件 (TopNav)。
 * 渲染路径面包屑导航、登录用户信息与全局快速登出交互。
 *
 * @returns {React.ReactElement} 顶部导航栏
 */
export function TopNav() {
  const pathname = usePathname();
  const session = useSessionContext();
  const { email } = useUserEmail();
  const { labels } = useBreadcrumb();
  const crumbs = getBreadcrumbs(pathname, labels);

  const handleSignOut = async () => {
    await signOut();
    window.location.href = "/";
  };

  const displayName = email || (!session.loading ? session.userId : "") || "";
  const isLoggedIn = !session.loading && session.doesSessionExist;

  return (
    <header className="flex h-14 items-center justify-between border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0a0f1d] px-4 lg:px-6 transition-colors">
      {/* Breadcrumbs */}
      <nav className="flex items-center gap-1.5 text-xs sm:text-sm font-medium text-slate-500 dark:text-slate-400">
        <Link href="/dashboard" className="hover:text-slate-900 dark:hover:text-white transition-colors">
          Home
        </Link>
        {crumbs.slice(1).map((crumb) => (
          <span key={crumb.href} className="flex items-center gap-1.5">
            <ChevronRight className="h-3.5 w-3.5 text-slate-400 dark:text-slate-600" />
            <Link
              href={crumb.href}
              className="hover:text-slate-900 dark:hover:text-white transition-colors"
            >
              {crumb.label}
            </Link>
          </span>
        ))}
      </nav>

      {/* Right side */}
      <div className="flex items-center gap-3">
        {isLoggedIn && (
          <>
            <span className="text-xs font-semibold text-slate-600 dark:text-slate-300 hidden sm:inline px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
              {displayName}
            </span>
            <button
              onClick={handleSignOut}
              className="p-1.5 rounded-md text-slate-500 hover:text-red-600 dark:hover:text-red-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              title="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </>
        )}
      </div>
    </header>
  );
}

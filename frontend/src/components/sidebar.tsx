"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { 
  LayoutDashboard, 
  FlaskConical, 
  CreditCard, 
  HelpCircle, 
  Moon, 
  Sun, 
  LogOut, 
  Database,
  Layers
} from "lucide-react";
import { useSessionContext } from "supertokens-auth-react/recipe/session";
import { signOut } from "supertokens-auth-react/recipe/thirdparty";
import { useTheme } from "@/components/theme-provider";
import { useUserEmail } from "@/lib/use-user-email";

/**
 * 工作区核心导航定义
 */
const mainNavItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/studies", label: "Studies", icon: FlaskConical },
  { href: "/knowledge", label: "Knowledge Base", icon: Database },
];

/**
 * 系统与支持导航定义
 */
const secondaryNavItems = [
  { href: "/billing", label: "Billing", icon: CreditCard },
  { href: "/help", label: "Help & FAQ", icon: HelpCircle },
];

/**
 * 侧边栏工作台组件 (遵循 Palantir Prussian Navy & Slate 工业级设计规范)。
 * 提供模块化分组导航、严谨的品牌徽章标识、深浅主题切换与租户身份展示。
 *
 * @returns {React.ReactElement} 侧边栏元素
 */
export function Sidebar() {
  const pathname = usePathname();
  const session = useSessionContext();
  const { email } = useUserEmail();
  const { setTheme, resolved } = useTheme();

  const handleSignOut = async () => {
    await signOut();
    window.location.href = "/";
  };

  const displayName = email || (!session.loading ? session.userId : "") || "";
  const isLoggedIn = !session.loading && session.doesSessionExist;

  /**
   * 动态计算导航条目的高亮样式类
   *
   * @param {boolean} isActive 是否为当前激活路径
   * @returns {string} 组合样式类名
   */
  const getNavItemClass = (isActive: boolean): string =>
    `flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-all group ${
      isActive
        ? "bg-slate-100 dark:bg-slate-800 text-[#1e3a8a] dark:text-[#93c5fd] font-bold"
        : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100/70 dark:hover:bg-slate-800/60 font-medium"
    }`;

  return (
    <aside className="hidden md:flex flex-col w-64 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0a0f1d] text-slate-800 dark:text-slate-200 flex-shrink-0 select-none transition-colors">
      {/* ── Brand Workspace Header ── */}
      <div className="flex h-14 items-center justify-between border-b border-slate-200 dark:border-slate-800 px-4">
        <div className="flex items-center gap-2.5">
          <div className="h-7 w-7 rounded-md bg-[#1e3a8a] dark:bg-[#1e40af] text-white flex items-center justify-center font-bold text-xs shadow-xs">
            <Layers className="h-4 w-4" />
          </div>
          <span className="font-bold text-sm tracking-tight text-slate-900 dark:text-slate-100">
            TLF Studio
          </span>
        </div>
        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
          CDISC
        </span>
      </div>

      {/* ── Navigation Links ── */}
      <div className="flex-1 overflow-y-auto p-3 space-y-5">
        {/* Main Section */}
        <div>
          <h4 className="px-3 text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1.5">
            Overview
          </h4>
          <nav className="space-y-1">
            {mainNavItems.map((item) => {
              const isActive = pathname.startsWith(item.href);
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={getNavItemClass(isActive)}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </div>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Secondary Section */}
        <div>
          <h4 className="px-3 text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1.5">
            Settings & Support
          </h4>
          <nav className="space-y-1">
            {secondaryNavItems.map((item) => {
              const isActive = pathname.startsWith(item.href);
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={getNavItemClass(isActive)}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </div>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* ── Bottom Section ── */}
      <div className="border-t border-slate-200 dark:border-slate-800 p-3 space-y-2 bg-slate-50/50 dark:bg-[#070b14]/50">
        {/* Theme Toggle Button */}
        <button
          onClick={() => setTheme(resolved === "dark" ? "light" : "dark")}
          className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
        >
          <div className="flex items-center gap-2.5">
            {resolved === "dark" ? (
              <Sun className="h-3.5 w-3.5 text-amber-500" />
            ) : (
              <Moon className="h-3.5 w-3.5 text-[#1e3a8a]" />
            )}
            <span>{resolved === "dark" ? "Light Mode" : "Dark Mode"}</span>
          </div>
          <span className="text-[10px] uppercase tracking-wider text-slate-400 font-mono">
            {resolved}
          </span>
        </button>

        {/* User Profile Card */}
        {isLoggedIn && (
          <div className="flex items-center justify-between rounded-lg p-2 bg-white dark:bg-[#101828] border border-slate-200 dark:border-slate-800 shadow-xs">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800 text-[#1e3a8a] dark:text-[#93c5fd] font-bold text-xs border border-slate-200 dark:border-slate-700">
                {displayName.charAt(0).toUpperCase()}
              </div>
              <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 truncate max-w-[130px]">
                {displayName}
              </span>
            </div>
            <button
              onClick={handleSignOut}
              className="p-1 rounded text-slate-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              title="Sign out"
            >
              <LogOut className="h-3.5 w-3.5" />
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}

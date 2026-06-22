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
    <header className="flex h-14 items-center justify-between border-b bg-background px-4 lg:px-6">
      {/* Breadcrumbs */}
      <nav className="flex items-center gap-1 text-sm text-muted-foreground">
        <Link href="/dashboard" className="hover:text-foreground transition-colors">
          Home
        </Link>
        {crumbs.slice(1).map((crumb) => (
          <span key={crumb.href} className="flex items-center gap-1">
            <ChevronRight className="h-3 w-3" />
            <Link
              href={crumb.href}
              className="hover:text-foreground transition-colors"
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
            <span className="text-sm text-muted-foreground hidden sm:inline">
              {displayName}
            </span>
            <button
              onClick={handleSignOut}
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </>
        )}
      </div>
    </header>
  );
}

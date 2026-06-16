"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { useUser, useStackApp } from "@hexclave/next";
import { ChevronRight, LogOut } from "lucide-react";
import { Button } from "@hexclave/ui";
import { cn } from "@hexclave/ui";

function getBreadcrumbs(pathname: string): { label: string; href: string }[] {
  const parts = pathname.split("/").filter(Boolean);
  const crumbs: { label: string; href: string }[] = [];
  let href = "";

  for (const part of parts) {
    href += "/" + part;
    // Skip dynamic segments for label
    if (part.startsWith("[")) continue;
    // Pretty label
    const label = part
      .replace(/-/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
    crumbs.push({ label, href });
  }
  return crumbs;
}

export function TopNav() {
  const pathname = usePathname();
  const user = useUser();
  const app = useStackApp();
  const crumbs = getBreadcrumbs(pathname);

  const handleSignOut = async () => {
    await app.signOut();
    window.location.href = "/";
  };

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
        {user && (
          <>
            <span className="text-sm text-muted-foreground hidden sm:inline">
              {user.displayName || user.primaryEmail}
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

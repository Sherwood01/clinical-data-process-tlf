"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { LayoutDashboard, FlaskConical, Moon, Sun, LogOut } from "lucide-react";
import { useSessionContext } from "supertokens-auth-react/recipe/session";
import { signOut } from "supertokens-auth-react/recipe/thirdpartyemailpassword";
import { useTheme } from "@/components/theme-provider";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/studies", label: "Studies", icon: FlaskConical },
];

export function Sidebar() {
  const pathname = usePathname();
  const session = useSessionContext();
  const { theme, setTheme, resolved } = useTheme();

  const handleSignOut = async () => {
    await signOut();
    window.location.href = "/";
  };

  const displayName = session.accessTokenPayload?.email || session.userId || "";
  const isLoggedIn = !session.loading && session.doesSessionExist;

  return (
    <aside className="hidden md:flex flex-col w-64 border-r bg-sidebar text-sidebar-foreground flex-shrink-0">
      {/* Logo */}
      <div className="flex h-14 items-center gap-2 border-b border-sidebar-border px-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground text-sm font-bold">
          T
        </div>
        <span className="font-semibold text-sm">TLF Report</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-3">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              style={{
                backgroundColor: isActive ? "var(--sidebar-accent)" : "transparent",
                color: isActive ? "var(--sidebar-accent-foreground)" : "var(--sidebar-foreground)",
                opacity: isActive ? 1 : 0.7,
              }}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Bottom section */}
      <div className="border-t border-sidebar-border p-3 space-y-2">
        {/* Theme toggle */}
        <button
          onClick={() => setTheme(resolved === "dark" ? "light" : "dark")}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm opacity-70 hover:opacity-100 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
        >
          {resolved === "dark" ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
          {resolved === "dark" ? "Light Mode" : "Dark Mode"}
        </button>

        {/* User info */}
        {isLoggedIn && (
          <div className="flex items-center justify-between rounded-lg px-3 py-2">
            <div className="flex items-center gap-3 min-w-0">
              <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-medium">
                {displayName.charAt(0).toUpperCase()}
              </div>
              <span className="text-sm truncate">
                {displayName}
              </span>
            </div>
            <button
              onClick={handleSignOut}
              className="flex-shrink-0 opacity-50 hover:opacity-100 transition-opacity"
              title="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}

"use client";

import { useSessionContext } from "supertokens-auth-react/recipe/session";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export function AuthWrapper({ children }: { children: React.ReactNode }) {
  const session = useSessionContext();

  // Show nothing while session is loading (avoids flash)
  if (session.loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-background to-muted/50 px-4">
        <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-background to-muted/50 px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="mb-8 text-center">
          <Link href="/" className="inline-flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground text-sm font-bold">
              T
            </div>
            <span className="font-semibold">TLF Report</span>
          </Link>
        </div>

        {/* No outer card — SuperTokens renders its own styled container */}
        <div>
          {children}
        </div>

        {/* Back link */}
        <div className="mt-6 text-center">
          <Link
            href="/"
            className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-3 w-3" />
            Back to home
          </Link>
        </div>
      </div>
    </div>
  );
}

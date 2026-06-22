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

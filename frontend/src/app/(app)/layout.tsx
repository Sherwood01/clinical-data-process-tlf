"use client";

import { Suspense } from "react";
import { AppShell } from "@/components/app-shell";

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
      <AppShell>{children}</AppShell>
    </Suspense>
  );
}

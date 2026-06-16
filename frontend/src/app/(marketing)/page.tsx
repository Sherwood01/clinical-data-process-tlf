"use client";

import { Suspense } from "react";
import { LandingPage } from "@/components/landing-page";

export default function HomePage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    }>
      <LandingPage />
    </Suspense>
  );
}

"use client";

import { Suspense } from "react";
import dynamic from "next/dynamic";

const DashboardContent = dynamic(
  () => import("@/components/dashboard-content"),
  { ssr: false }
);

export default function DashboardPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-gray-500">Loading...</div>}>
      <DashboardContent />
    </Suspense>
  );
}

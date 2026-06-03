"use client";

import { Suspense } from "react";
import dynamic from "next/dynamic";

const StudyDetailContent = dynamic(
  () => import("@/components/studies/study-detail-content"),
  { ssr: false }
);

export default function StudyDetailPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-gray-500">Loading...</div>}>
      <StudyDetailContent />
    </Suspense>
  );
}

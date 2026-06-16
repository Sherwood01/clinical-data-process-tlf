"use client";

import { Suspense } from "react";
import dynamic from "next/dynamic";

const StudyDetailContent = dynamic(
  () => import("@/components/studies/study-detail-content"),
  { ssr: false }
);

export default function StudyDetailPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-[60vh] items-center justify-center text-muted-foreground">
          Loading...
        </div>
      }
    >
      <StudyDetailContent />
    </Suspense>
  );
}

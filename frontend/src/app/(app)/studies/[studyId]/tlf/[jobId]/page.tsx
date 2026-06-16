"use client";

import { Suspense } from "react";
import dynamic from "next/dynamic";

const PDFViewer = dynamic(
  () => import("@/components/studies/pdf-viewer"),
  { ssr: false }
);

export default function PDFViewerPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-[60vh] items-center justify-center text-muted-foreground">
          Loading...
        </div>
      }
    >
      <PDFViewer />
    </Suspense>
  );
}

"use client";

import { Suspense } from "react";
import dynamic from "next/dynamic";

const PDFViewer = dynamic(
  () => import("@/components/studies/pdf-viewer"),
  { ssr: false }
);

export default function TLFPreviewPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-gray-500">Loading...</div>}>
      <PDFViewer />
    </Suspense>
  );
}

"use client";

import { Suspense } from "react";
import dynamic from "next/dynamic";

const KnowledgeContent = dynamic(
  () => import("@/components/knowledge-content"),
  { ssr: false }
);

export default function KnowledgePage() {
  return (
    <Suspense fallback={
      <div className="min-h-[80vh] flex flex-col items-center justify-center text-gray-500 gap-3">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
        <p className="text-sm">Loading clinical knowledge base console...</p>
      </div>
    }>
      <KnowledgeContent />
    </Suspense>
  );
}

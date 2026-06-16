"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { TOCSelector } from "./toc-selector";

interface TLFGeneratorProps {
  studyId: string;
  tocEntries: any[];
  jobs: any[];
  onRefresh: () => void;
  getAccessToken: () => Promise<string | null>;
}

export function TLFGenerator({
  studyId,
  tocEntries,
  jobs,
  onRefresh,
  getAccessToken,
}: TLFGeneratorProps) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [generating, setGenerating] = useState(false);
  const [activeJobIds, setActiveJobIds] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const pollingRef = useRef<Map<string, number>>(new Map());

  // Poll active jobs
  useEffect(() => {
    if (activeJobIds.size === 0) return;

    const interval = setInterval(async () => {
      const token = await getAccessToken();
      for (const jobId of activeJobIds) {
        try {
          const res = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/tlf/${jobId}`,
            {
              headers: { Authorization: `Bearer ${token}` },
            }
          );
          if (res.ok) {
            const job = await res.json();
            if (job.status === "completed" || job.status === "failed") {
              setActiveJobIds((prev) => {
                const next = new Set(prev);
                next.delete(jobId);
                return next;
              });
              onRefresh();
            }
          }
        } catch (err) {
          console.error("Polling error:", err);
        }
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [activeJobIds, studyId, getAccessToken, onRefresh]);

  const handleGenerate = useCallback(async () => {
    if (selectedIds.size === 0) return;
    setGenerating(true);
    setError(null);

    try {
      const token = await getAccessToken();
      const newJobIds: string[] = [];

      for (const tocEntryId of selectedIds) {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/tlf/generate`,
          {
            method: "POST",
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              toc_entry_id: tocEntryId,
            }),
          }
        );

        if (res.ok) {
          const job = await res.json();
          newJobIds.push(job.id);
        } else {
          const text = await res.text();
          console.error(`Failed to generate TLF for ${tocEntryId}: ${text}`);
        }
      }

      if (newJobIds.length > 0) {
        setActiveJobIds((prev) => {
          const next = new Set(prev);
          newJobIds.forEach((id) => next.add(id));
          return next;
        });
        setSelectedIds(new Set());
        onRefresh();
      }
    } catch (err: any) {
      setError(err.message || "Generation failed");
    } finally {
      setGenerating(false);
    }
  }, [selectedIds, studyId, getAccessToken, onRefresh]);

  const pendingJobs = jobs.filter(
    (j: any) => j.status === "pending" || j.status === "running"
  );


  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">TLF Generator</h2>

      {/* Active generation status */}
      {(activeJobIds.size > 0 || pendingJobs.length > 0) && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-3 h-3 rounded-full bg-blue-500 animate-pulse" />
            <span className="text-sm font-medium text-blue-700">
              Generation in progress
            </span>
          </div>
          <p className="text-xs text-blue-600">
            {activeJobIds.size} job(s) running. The page will update
            automatically when complete.
          </p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-sm text-red-700">{error}</p>
          <button
            onClick={() => setError(null)}
            className="text-xs text-red-500 hover:underline mt-1"
          >
            Dismiss
          </button>
        </div>
      )}

        <>
          {/* TOC Selector */}
          <div className="bg-white border rounded-lg p-6 mb-6">
            <h3 className="font-medium mb-2">Select TOC Entries to Generate</h3>
            <p className="text-sm text-gray-500 mb-4">
              Choose the TOC entries you want to generate TLF reports for. Only
              entries that have not been generated yet are selectable.
            </p>
            <TOCSelector
              entries={tocEntries}
              selectedIds={selectedIds}
              onSelectionChange={setSelectedIds}
            />
          </div>

          {/* Generate button */}
          <div className="flex items-center justify-between">
            <button
              onClick={handleGenerate}
              disabled={selectedIds.size === 0 || generating}
              className={`px-6 py-3 rounded-lg text-sm font-medium transition-colors ${
                selectedIds.size === 0 || generating
                  ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                  : "bg-blue-600 text-white hover:bg-blue-700"
              }`}
            >
              {generating
                ? "Starting jobs..."
                : `Generate Selected (${selectedIds.size})`}
            </button>
            <span className="text-xs text-gray-500">
              {tocEntries.filter((e: any) => !e.is_generated).length} entries pending,{" "}
              {tocEntries.filter((e: any) => e.is_generated).length} generated
            </span>
          </div>
        </>
    </div>
  );
}

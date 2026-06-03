"use client";

import { useStackApp, useUser } from "@hexclave/next";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function PDFViewer() {
  const app = useStackApp();
  const user = useUser();
  const router = useRouter();
  const params = useParams<{ studyId: string; jobId: string }>();
  const studyId = params?.studyId;
  const jobId = params?.jobId;

  const [job, setJob] = useState<any>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user === undefined) return;
    if (user === null || !studyId || !jobId) {
      router.push("/handler/sign-in");
      return;
    }
    fetchJob();
  }, [user, studyId, jobId]);

  async function fetchJob() {
    if (!studyId || !jobId) return;
    try {
      const token = await app.getAccessToken();
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/tlf/${jobId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (res.ok) {
        const data = await res.json();
        setJob(data);

        // Generate download URL
        if (data.status === "completed" && data.tlf_outputs?.length > 0) {
          const downloadRes = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/tlf/${jobId}/download`,
            { headers: { Authorization: `Bearer ${token}` } }
          );
          if (downloadRes.ok) {
            const { url } = await downloadRes.json();
            setPdfUrl(url);
          }
        }
      } else {
        setError("Job not found");
      }
    } catch (err: any) {
      setError(err.message || "Failed to load job");
    } finally {
      setLoading(false);
    }
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push(`/studies/${studyId}`)}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              &larr; Back to Study
            </button>
            <h1 className="font-bold text-lg">
              {job?.tlf_id || "Report"} - Preview
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">
              {user.displayName || user.primaryEmail}
            </span>
            <button
              onClick={() => app.signOut()}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 container mx-auto px-4 py-6">
        {loading ? (
          <div className="text-center py-12 text-gray-500">Loading...</div>
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-red-600">{error}</p>
            <button
              onClick={() => router.push(`/studies/${studyId}`)}
              className="text-blue-600 hover:underline text-sm mt-2"
            >
              Return to study
            </button>
          </div>
        ) : job?.status === "completed" && pdfUrl ? (
          <div>
            {/* Download button */}
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="font-semibold">
                  {job.tlf_id} - {job.tlf_name}
                </h2>
                {job.tlf_type && (
                  <span className="text-xs text-gray-500">
                    Type: {job.tlf_type}
                  </span>
                )}
              </div>
              <a
                href={pdfUrl}
                download
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm font-medium"
              >
                Download PDF
              </a>
            </div>

            {/* PDF iframe */}
            <div className="bg-white border rounded-lg overflow-hidden">
              <iframe
                src={pdfUrl}
                className="w-full"
                style={{ height: "calc(100vh - 220px)" }}
                title="PDF Preview"
              />
            </div>
          </div>
        ) : job?.status === "running" || job?.status === "pending" ? (
          <div className="text-center py-16">
            <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Report is being generated</h2>
            <p className="text-gray-500 mb-4">
              This page will automatically update when the report is ready.
            </p>
            <button
              onClick={fetchJob}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm"
            >
              Refresh
            </button>
          </div>
        ) : job?.status === "failed" ? (
          <div className="text-center py-16">
            <div className="text-4xl mb-4">❌</div>
            <h2 className="text-xl font-semibold mb-2">Generation Failed</h2>
            <p className="text-red-600 mb-4">
              {job.error_message || "An unknown error occurred"}
            </p>
            <button
              onClick={() => router.push(`/studies/${studyId}?tab=tlf`)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm"
            >
              Try Again
            </button>
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500">
            No report available for this job.
          </div>
        )}
      </main>
    </div>
  );
}

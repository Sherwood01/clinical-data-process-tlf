"use client";

import { useSessionContext } from "supertokens-auth-react/recipe/session";
import { getAccessToken } from "supertokens-web-js/recipe/session";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useUserEmail } from "@/lib/use-user-email";
import { useBreadcrumb } from "@/lib/breadcrumb-context";
import { StudyOverview } from "./study-overview";
import { DatasetUpload } from "./dataset-upload";
import { SAPUpload } from "./sap-upload";
import { TOCSelector } from "./toc-selector";
import { TLFGenerator } from "./tlf-generator";
import { Eye, FileText, Copy, X, Loader2 } from "lucide-react";

type Tab = "overview" | "datasets" | "sap" | "tlf" | "history";

export default function StudyDetailContent() {
  const session = useSessionContext();
  const router = useRouter();
  const params = useParams<{ studyId: string }>();
  const studyId = params?.studyId;

  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [study, setStudy] = useState<any>(null);
  const [datasets, setDatasets] = useState<any[]>([]);
  const [sapDocs, setSapDocs] = useState<any[]>([]);
  const [tocEntries, setTocEntries] = useState<any[]>([]);
  const [tlfJobs, setTlfJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const { email } = useUserEmail();
  const { setBreadcrumbLabel } = useBreadcrumb();

  useEffect(() => {
    if (session.loading) return;
    if (!session.doesSessionExist || !studyId) {
      router.push("/auth/sign-in");
      return;
    }
    fetchStudyData();
  }, [session.loading, session, studyId]);

  async function fetchStudyData() {
    if (!studyId) return;
    try {
      const token = await getAccessToken();
      const headers = { Authorization: `Bearer ${token}` };

      const [studyRes, datasetsRes, sapRes, tocRes, jobsRes] = await Promise.all([
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}`, { headers }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/datasets`, { headers }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/sap`, { headers }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/sap/toc`, { headers }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/tlf`, { headers }),
      ]);

      if (studyRes.ok) {
        const studyData = await studyRes.json();
        setStudy(studyData);
        if (studyId && studyData.name) {
          setBreadcrumbLabel(studyId, studyData.name);
        }
      }
      if (datasetsRes.ok) setDatasets(await datasetsRes.json());
      if (sapRes.ok) setSapDocs(await sapRes.json());
      if (tocRes.ok) setTocEntries(await tocRes.json());
      if (jobsRes.ok) setTlfJobs(await jobsRes.json());
    } catch (err) {
      console.error("Failed to fetch study data:", err);
    } finally {
      setLoading(false);
    }
  }

  if (session.loading) return null;
  if (!session.doesSessionExist || !studyId) return null;

  const tabs: { key: Tab; label: string }[] = [
    { key: "overview", label: "Overview" },
    { key: "datasets", label: "Datasets" },
    { key: "sap", label: "SAP & TOC" },
    { key: "tlf", label: "TLF Generator" },
    { key: "history", label: "History" },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push("/dashboard")}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              &larr; Back
            </button>
            <h1 className="font-bold text-lg">
              {study?.name || "Loading..."}
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">
              {email || (!session.loading ? session.userId : "") || ""}
            </span>
          </div>
        </div>
      </header>

      {/* Tab navigation */}
      <div className="border-b bg-white">
        <div className="container mx-auto px-4">
          <nav className="-mb-px flex gap-6">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`py-3 text-sm font-semibold border-b-4 transition-all duration-200 ${
                  activeTab === tab.key
                    ? "!border-blue-600 text-blue-600 font-bold"
                    : "!border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      <main className="container mx-auto px-4 py-6">
        {loading ? (
          <div className="text-center py-12 text-gray-500">Loading...</div>
        ) : (
          <>
            {activeTab === "overview" && (
              <StudyOverview
                study={study}
                datasets={datasets}
                tocEntries={tocEntries}
                tlfJobs={tlfJobs}
                onRefresh={() => fetchStudyData()}
                getAccessToken={getAccessToken}
              />
            )}
            {activeTab === "datasets" && (
              <DatasetUpload
                studyId={studyId}
                datasets={datasets}
                onRefresh={() => fetchStudyData()}
                getAccessToken={getAccessToken}
              />
            )}
            {activeTab === "sap" && (
              <SAPUpload
                studyId={studyId}
                sapDocs={sapDocs}
                tocEntries={tocEntries}
                onRefresh={() => fetchStudyData()}
                getAccessToken={getAccessToken}
              />
            )}
            {activeTab === "tlf" && (
              <TLFGenerator
                studyId={studyId}
                tocEntries={tocEntries}
                jobs={tlfJobs}
                onRefresh={() => fetchStudyData()}
                getAccessToken={getAccessToken}
              />
            )}
            {activeTab === "history" && (
              <TLFHistory
                jobs={tlfJobs}
                studyId={studyId}
                getAccessToken={getAccessToken}
              />
            )}
          </>
        )}
      </main>
    </div>
  );
}

function TLFHistory({
  jobs,
  studyId,
  getAccessToken,
}: {
  jobs: any[];
  studyId: string;
  getAccessToken: () => Promise<string | undefined>;
}) {
  const router = useRouter();
  const [previewJob, setPreviewJob] = useState<any>(null);
  const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [failedJobLog, setFailedJobLog] = useState<any>(null);
  const [copied, setCopied] = useState(false);

  const handlePreview = async (job: any) => {
    setPreviewJob(job);
    setPreviewLoading(true);
    setPdfBlobUrl(null);
    try {
      const token = await getAccessToken();
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/tlf/${job.id}/content`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        setPdfBlobUrl(url);
      } else {
        const text = await res.text();
        alert(`Failed to fetch PDF content: ${text}`);
        setPreviewJob(null);
      }
    } catch (err: any) {
      alert(`Error previewing PDF: ${err.message}`);
      setPreviewJob(null);
    } finally {
      setPreviewLoading(false);
    }
  };

  const closePreview = () => {
    if (pdfBlobUrl) {
      URL.revokeObjectURL(pdfBlobUrl);
      setPdfBlobUrl(null);
    }
    setPreviewJob(null);
  };

  const handleCopyLog = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (jobs.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No TLF generation jobs yet. Go to the TLF Generator tab to create one.
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">Generation History</h2>
      <div className="bg-white border rounded-lg overflow-hidden shadow-sm">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Job ID</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">TOC Entry</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Progress</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Created</th>
              <th className="text-center px-4 py-3 font-medium text-gray-600">Preview</th>
              <th className="text-right px-4 py-3 font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {jobs.map((job: any) => (
              <tr key={job.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-mono text-xs">{job.id.slice(0, 8)}...</td>
                <td className="px-4 py-3">{job.tlf_id || job.tlf_name || "-"}</td>
                <td className="px-4 py-3">
                  <StatusBadge
                    status={job.status}
                    onClick={() => {
                      if (job.status === "failed") {
                        setFailedJobLog(job);
                      }
                    }}
                  />
                </td>
                <td className="px-4 py-3 font-medium text-gray-700">
                  {job.progress != null ? `${Math.round(job.progress * 100)}%` : "-"}
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs font-medium">
                  {job.created_at ? new Date(job.created_at).toLocaleString() : "-"}
                </td>
                <td className="px-4 py-3 text-center">
                  {job.status === "completed" ? (
                    <button
                      onClick={() => handlePreview(job)}
                      className="inline-flex items-center gap-1 border border-gray-300 hover:bg-gray-50 text-gray-700 px-2.5 py-1 rounded text-xs font-semibold shadow-sm transition-all"
                    >
                      <Eye className="h-3 w-3 text-gray-500" /> Preview
                    </button>
                  ) : (
                    <span className="text-gray-300">-</span>
                  )}
                </td>
                <td className="px-4 py-3 text-right">
                  {job.status === "completed" ? (
                    <button
                      onClick={() =>
                        router.push(`/studies/${studyId}/tlf/${job.id}`)
                      }
                      className="text-blue-600 hover:underline text-xs font-semibold"
                    >
                      View Detail
                    </button>
                  ) : job.status === "failed" && job.error_message ? (
                    <button
                      onClick={() => setFailedJobLog(job)}
                      className="text-xs text-red-500 hover:underline font-semibold"
                    >
                      View Log
                    </button>
                  ) : (
                    <span className="text-gray-300">-</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* PDF Preview Modal */}
      {previewJob && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-5xl max-h-[90vh] flex flex-col animate-in fade-in zoom-in duration-200">
            {/* Header */}
            <div className="px-6 py-4 border-b flex justify-between items-center bg-gray-50 rounded-t-xl">
              <div>
                <h3 className="font-bold text-gray-900 text-lg flex items-center gap-2">
                  <FileText className="h-5 w-5 text-blue-600" /> Report Preview: {previewJob.tlf_id}
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">{previewJob.tlf_name}</p>
              </div>
              <button
                onClick={closePreview}
                className="text-gray-400 hover:text-gray-600 font-bold p-1.5 hover:bg-gray-100 rounded-lg text-sm transition-colors"
              >
                ✕
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto p-6 bg-gray-100/50 flex flex-col justify-center items-center min-h-[400px]">
              {previewLoading ? (
                <div className="flex flex-col items-center gap-3 py-20 text-gray-500">
                  <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                  <p className="text-sm font-medium">Fetching report from cloud storage...</p>
                </div>
              ) : pdfBlobUrl ? (
                <iframe
                  src={pdfBlobUrl}
                  className="w-full h-[60vh] border rounded-lg shadow-inner bg-white"
                  title="PDF Preview"
                />
              ) : (
                <p className="text-red-500 font-semibold">Failed to load report PDF preview.</p>
              )}
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t bg-gray-50 rounded-b-xl flex justify-end gap-3">
              {pdfBlobUrl && (
                <a
                  href={pdfBlobUrl}
                  download={`report_${previewJob.tlf_id || "download"}.pdf`}
                  className="bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 px-4 py-2 rounded-lg font-semibold text-sm transition-all"
                >
                  Download PDF
                </a>
              )}
              <button
                onClick={closePreview}
                className="bg-gray-950 hover:bg-gray-900 text-white px-5 py-2 rounded-lg font-semibold text-sm transition-all"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Failed Log Modal */}
      {failedJobLog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col animate-in fade-in zoom-in duration-200">
            {/* Header */}
            <div className="px-6 py-4 border-b flex justify-between items-center bg-red-50 rounded-t-xl">
              <div>
                <h3 className="font-bold text-red-900 text-lg flex items-center gap-2">
                  ❌ Job Execution Failed
                </h3>
                <p className="text-xs text-red-600 mt-0.5 font-mono">Job ID: {failedJobLog.id}</p>
              </div>
              <button
                onClick={() => setFailedJobLog(null)}
                className="text-gray-400 hover:text-gray-600 font-bold p-1.5 hover:bg-gray-100 rounded-lg text-sm transition-colors"
              >
                ✕
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto p-6 bg-gray-50/50">
              <h4 className="font-semibold text-sm text-gray-700 mb-2">Failure Details & Logs:</h4>
              <pre className="bg-gray-950 text-red-400 p-4 rounded-lg overflow-auto font-mono text-xs whitespace-pre-wrap max-h-[40vh] border border-red-100 shadow-inner">
                {failedJobLog.error_message || "No error details logged."}
              </pre>
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t bg-gray-50 rounded-b-xl flex justify-end gap-3">
              <button
                onClick={() => handleCopyLog(failedJobLog.error_message || "")}
                className="bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 px-4 py-2 rounded-lg font-semibold text-sm transition-all flex items-center gap-1.5"
              >
                <Copy className="h-4 w-4" /> {copied ? "Copied!" : "Copy Logs"}
              </button>
              <button
                onClick={() => setFailedJobLog(null)}
                className="bg-gray-950 hover:bg-gray-900 text-white px-5 py-2 rounded-lg font-semibold text-sm transition-all"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status, onClick }: { status: string; onClick?: () => void }) {
  const styles: Record<string, string> = {
    pending: "bg-gray-100 text-gray-700",
    running: "bg-blue-100 text-blue-700",
    completed: "bg-green-100 text-green-700",
    failed: "bg-red-100 text-red-700 cursor-pointer hover:bg-red-200 transition-colors",
  };
  return (
    <span
      onClick={onClick}
      className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium select-none ${
        styles[status] || "bg-gray-100 text-gray-700"
      }`}
      title={status === "failed" ? "Click to view failure logs" : undefined}
    >
      {status}
    </span>
  );
}

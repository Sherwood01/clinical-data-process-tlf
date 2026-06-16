"use client";

import { useStackApp, useUser } from "@hexclave/next";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { StudyOverview } from "./study-overview";
import { DatasetUpload } from "./dataset-upload";
import { SAPUpload } from "./sap-upload";
import { TOCSelector } from "./toc-selector";
import { TLFGenerator } from "./tlf-generator";

type Tab = "overview" | "datasets" | "sap" | "tlf" | "history";

export default function StudyDetailContent() {
  const app = useStackApp();
  const user = useUser();
  const router = useRouter();
  const params = useParams<{ studyId: string }>();
  const studyId = params?.studyId;

  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [study, setStudy] = useState<any>(null);
  const [datasets, setDatasets] = useState<any[]>([]);
  const [tocEntries, setTocEntries] = useState<any[]>([]);
  const [tlfJobs, setTlfJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user === undefined) return;
    if (user === null || !studyId) {
      router.push("/handler/sign-in");
      return;
    }
    fetchStudyData();
  }, [user?.id, user === null, studyId]);

  async function fetchStudyData() {
    if (!studyId) return;
    try {
      const token = await app.getAccessToken();
      const headers = { Authorization: `Bearer ${token}` };

      const [studyRes, datasetsRes, tocRes, jobsRes] = await Promise.all([
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}`, { headers }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/datasets`, { headers }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/sap/toc`, { headers }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/tlf`, { headers }),
      ]);

      if (studyRes.ok) setStudy(await studyRes.json());
      if (datasetsRes.ok) setDatasets(await datasetsRes.json());
      if (tocRes.ok) setTocEntries(await tocRes.json());
      if (jobsRes.ok) setTlfJobs(await jobsRes.json());
    } catch (err) {
      console.error("Failed to fetch study data:", err);
    } finally {
      setLoading(false);
    }
  }

  if (!user || !studyId) return null;

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
            {study?.protocol_id && (
              <span className="text-sm text-gray-500">{study.protocol_id}</span>
            )}
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

      {/* Tab navigation */}
      <div className="border-b bg-white">
        <div className="container mx-auto px-4">
          <nav className="flex gap-6">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.key
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700"
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
              />
            )}
            {activeTab === "datasets" && (
              <DatasetUpload
                studyId={studyId}
                datasets={datasets}
                onRefresh={() => fetchStudyData()}
                getAccessToken={() => app.getAccessToken()}
              />
            )}
            {activeTab === "sap" && (
              <SAPUpload
                studyId={studyId}
                tocEntries={tocEntries}
                onRefresh={() => fetchStudyData()}
                getAccessToken={() => app.getAccessToken()}
              />
            )}
            {activeTab === "tlf" && (
              <TLFGenerator
                studyId={studyId}
                tocEntries={tocEntries}
                jobs={tlfJobs}
                onRefresh={() => fetchStudyData()}
                getAccessToken={() => app.getAccessToken()}
              />
            )}
            {activeTab === "history" && (
              <TLFHistory
                jobs={tlfJobs}
                studyId={studyId}
                getAccessToken={() => app.getAccessToken()}
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
  getAccessToken: () => Promise<string | null>;
}) {
  const router = useRouter();
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
      <div className="bg-white border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Job ID</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">TOC Entry</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Progress</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Created</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {jobs.map((job: any) => (
              <tr key={job.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-mono text-xs">{job.id.slice(0, 8)}...</td>
                <td className="px-4 py-3">{job.tlf_id || job.tlf_name || "-"}</td>
                <td className="px-4 py-3">
                  <StatusBadge status={job.status} />
                </td>
                <td className="px-4 py-3">
                  {job.progress != null ? `${Math.round(job.progress * 100)}%` : "-"}
                </td>
                <td className="px-4 py-3 text-gray-500">
                  {job.created_at ? new Date(job.created_at).toLocaleString() : "-"}
                </td>
                <td className="px-4 py-3">
                  {job.status === "completed" && (
                    <button
                      onClick={() =>
                        router.push(`/studies/${studyId}/tlf/${job.id}`)
                      }
                      className="text-blue-600 hover:underline text-xs"
                    >
                      View PDF
                    </button>
                  )}
                  {job.status === "failed" && job.error_message && (
                    <span className="text-xs text-red-500" title={job.error_message}>
                      Error
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending: "bg-gray-100 text-gray-700",
    running: "bg-blue-100 text-blue-700",
    completed: "bg-green-100 text-green-700",
    failed: "bg-red-100 text-red-700",
  };
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
        styles[status] || "bg-gray-100 text-gray-700"
      }`}
    >
      {status}
    </span>
  );
}

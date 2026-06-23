"use client";

import { useState } from "react";
import { Badge } from "@/components/ui";
import { Search, Table, Image, List, CheckSquare, Square, Eye, FileText, Copy, X, Loader2 } from "lucide-react";

interface TOCEntry {
  id: string;
  tlf_id: string;
  tlf_type: string;
  tlf_name: string;
  population: string;
  analysis_type: string;
  is_generated: boolean;
}

interface TOCSelectorProps {
  entries: TOCEntry[];
  selectedIds: Set<string>;
  onSelectionChange: (ids: Set<string>) => void;
  isStudyActive?: boolean;
  jobs?: any[];
  studyId?: string;
  getAccessToken?: () => Promise<string | undefined>;
  onNavigateToTab?: (tab: string) => void;
}

function TypeBadge({ type }: { type: string }) {
  const isTable = type === "table";
  const isFigure = type === "figure";
  
  const bgClass = isTable 
    ? "bg-blue-100 text-blue-700 border-blue-200" 
    : isFigure 
    ? "bg-purple-100 text-purple-700 border-purple-200" 
    : "bg-amber-100 text-amber-700 border-amber-200";

  const Icon = isTable ? Table : isFigure ? Image : List;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${bgClass}`}>
      <Icon className="h-3.5 w-3.5" />
      <span className="capitalize">{type}</span>
    </span>
  );
}

export function TOCSelector({
  entries,
  selectedIds,
  onSelectionChange,
  isStudyActive = true,
  jobs = [],
  studyId,
  getAccessToken,
  onNavigateToTab,
}: TOCSelectorProps) {
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");

  // 报告 PDF 预览 State
  const [previewJob, setPreviewJob] = useState<any>(null);
  const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  // 失败日志查看 State
  const [failedJobLog, setFailedJobLog] = useState<any>(null);
  const [copied, setCopied] = useState(false);

  // 根据当前 Job 历史联立推导状态
  const getEntryJobStatus = (entryId: string, entryIsGenerated: boolean) => {
    if (!jobs || jobs.length === 0) {
      return entryIsGenerated 
        ? { status: "generated", job: null } 
        : { status: "draft", job: null };
    }
    
    const entryJobs = jobs.filter((j: any) => j.toc_entry_id === entryId);
    if (entryJobs.length === 0) {
      return entryIsGenerated 
        ? { status: "generated", job: null } 
        : { status: "draft", job: null };
    }

    // 优先：查询是否存在活跃状态（排队或运行中）的任务
    const activeJob = entryJobs.find((j: any) => j.status === "running" || j.status === "pending");
    if (activeJob) {
      return { status: activeJob.status, job: activeJob };
    }

    // 次之：按时间降序找 Completed / Failed
    const sorted = [...entryJobs]
      .filter((j: any) => j.status === "completed" || j.status === "failed")
      .sort((a, b) => {
        const timeA = a.created_at ? new Date(a.created_at).getTime() : 0;
        const timeB = b.created_at ? new Date(b.created_at).getTime() : 0;
        return timeB - timeA;
      });
    
    if (sorted.length > 0) {
      const latest = sorted[0];
      const status = latest.status === "completed" ? "generated" : "failed";
      return { status, job: latest };
    }

    // 默认降级
    return entryIsGenerated 
      ? { status: "generated", job: null } 
      : { status: "draft", job: null };
  };

  const handlePreview = async (job: any) => {
    if (!job || !getAccessToken || !studyId) return;
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

  const filteredEntries = entries.filter((e) => {
    if (typeFilter !== "all" && e.tlf_type !== typeFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        e.tlf_id.toLowerCase().includes(q) ||
        e.tlf_name.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const toggleEntry = (id: string) => {
    if (!isStudyActive) return;
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    onSelectionChange(next);
  };

  const selectAll = () => {
    onSelectionChange(new Set(filteredEntries.map((e) => e.id)));
  };

  const deselectAll = () => {
    onSelectionChange(new Set());
  };

  const filterTypes = ["all", "table", "figure", "listing"];

  return (
    <div>
      {/* Filters */}
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <div className="flex gap-1 bg-muted rounded-lg p-1">
          {filterTypes.map((type) => (
            <button
              key={type}
              onClick={() => setTypeFilter(type)}
              className={`px-3 py-1.5 text-xs rounded-md font-medium transition-colors ${
                typeFilter === type
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          ))}
        </div>
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search TLF ID or name..."
            className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring pl-8"
          />
        </div>
        <span className="text-xs text-muted-foreground whitespace-nowrap">
          {selectedIds.size} selected
        </span>
      </div>

      {/* Select / Deselect all */}
      {isStudyActive && (
        <div className="flex items-center gap-3 mb-3">
          <button
            onClick={selectAll}
            className="text-xs text-primary hover:underline flex items-center gap-1"
          >
            <CheckSquare className="h-3 w-3" />
            Select All
          </button>
          <button
            onClick={deselectAll}
            className="text-xs text-muted-foreground hover:underline flex items-center gap-1"
          >
            <Square className="h-3 w-3" />
            Deselect All
          </button>
        </div>
      )}

      {/* Table */}
      <div className="rounded-xl border bg-card overflow-hidden max-h-96 overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 border-b sticky top-0">
            <tr>
              <th className="w-10 px-4 py-3"></th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">TLF ID</th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Type</th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Name</th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Population</th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {filteredEntries.map((entry) => (
              <tr
                key={entry.id}
                className={`transition-colors ${
                  isStudyActive ? "hover:bg-muted/30 cursor-pointer" : "opacity-80"
                }`}
                onClick={() => isStudyActive && toggleEntry(entry.id)}
              >
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={selectedIds.has(entry.id)}
                    onChange={() => isStudyActive && toggleEntry(entry.id)}
                    disabled={!isStudyActive}
                    className="rounded border-input text-primary focus:ring-primary h-4 w-4 disabled:opacity-50 disabled:cursor-not-allowed"
                  />
                </td>
                <td className="px-4 py-3 font-mono text-xs">{entry.tlf_id}</td>
                <td className="px-4 py-3">
                  <TypeBadge type={entry.tlf_type} />
                </td>
                <td className="px-4 py-3 max-w-xs truncate">{entry.tlf_name || "-"}</td>
                <td className="px-4 py-3 text-muted-foreground">{entry.population || "-"}</td>
                 <td className="px-4 py-3">
                   {(() => {
                     const { status, job } = getEntryJobStatus(entry.id, entry.is_generated);
                                          // 样式映射
                      const styles: Record<string, string> = {
                        draft: "bg-slate-100 text-slate-500 border-slate-200",
                        pending: "bg-amber-50 text-amber-600 border-amber-200",
                        running: "bg-blue-100 text-blue-700 border-blue-200 hover:bg-blue-200 cursor-pointer",
                        generated: "bg-emerald-100 text-emerald-700 border-emerald-200 hover:bg-emerald-200 cursor-pointer",
                        failed: "bg-red-100 text-red-700 border-red-200 hover:bg-red-200 cursor-pointer",
                      };

                     const handleClick = (e: React.MouseEvent) => {
                       e.stopPropagation(); // 阻止行点击 checkbox toggle 冒泡
                       if (status === "generated") {
                         // 点击 generated 时，如果找到了关联的 completed 任务进行预览
                         if (job) {
                           handlePreview(job);
                         } else {
                           // 兜底：如果 entry.is_generated 存在，但当前页面缓存的 jobs 列表中尚未匹配到具体 job
                           // 可以尝试通过 jobs 匹配这一个 entry 的 completed 状态 Job
                           const entryJobs = jobs.filter((j: any) => j.toc_entry_id === entry.id);
                           const completedJob = entryJobs.find((j: any) => j.status === "completed");
                           if (completedJob) {
                             handlePreview(completedJob);
                           } else {
                             alert("The report was generated, but the matching job history is not loaded. Please refresh.");
                           }
                         }
                       } else if (status === "failed" && job) {
                         setFailedJobLog(job);
                       } else if (status === "running") {
                         onNavigateToTab?.("history");
                       }
                     };

                     return (
                       <span
                         onClick={handleClick}
                         className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold border select-none transition-all ${
                           styles[status] || "bg-gray-100 text-gray-500 border-gray-200"
                         }`}
                         title={
                           status === "generated" ? "Click to preview PDF report" :
                           status === "failed" ? "Click to view execution error logs" :
                           status === "running" ? "Click to track progress in History" : undefined
                         }
                       >
                         {status}
                       </span>
                     );
                   })()}
                 </td>
              </tr>
            ))}
            {filteredEntries.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                  No matching TOC entries found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* PDF Preview Modal */}
      {previewJob && (
        <div className="fixed inset-0 bg-white z-50 flex flex-col animate-in fade-in duration-200 text-left">
          <div className="w-full h-full flex flex-col">
            {/* Header */}
            <div className="px-6 py-4 border-b flex justify-between items-center bg-gray-50 animate-in fade-in">
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
            <div className="flex-1 bg-gray-100/50 flex flex-col p-6 overflow-hidden">
              {previewLoading ? (
                <div className="flex flex-col items-center justify-center flex-1 gap-3 py-20 text-gray-500">
                  <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                  <p className="text-sm font-medium">Fetching report from cloud storage...</p>
                </div>
              ) : pdfBlobUrl ? (
                <iframe
                  src={pdfBlobUrl}
                  className="w-full h-full flex-1 border rounded-lg shadow-inner bg-white"
                  title="PDF Preview"
                />
              ) : (
                <div className="flex flex-col items-center justify-center flex-1 text-red-500 font-semibold">
                  Failed to load report PDF preview.
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t bg-gray-50 flex justify-end gap-3">
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
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col animate-in fade-in zoom-in duration-200 text-left">
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

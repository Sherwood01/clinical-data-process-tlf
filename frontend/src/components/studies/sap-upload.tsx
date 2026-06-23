"use client";

import { useState, useCallback, useEffect } from "react";
import dynamic from "next/dynamic";
import { FileUpload } from "./file-upload";
import { Trash2, Eye, FileText, Edit2, Loader2 } from "lucide-react";

const DocxRenderer = dynamic(() => import("./docx-renderer"), {
  ssr: false,
  loading: () => (
    <div className="flex flex-col items-center justify-center flex-1 text-gray-500 gap-3">
      <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      <p className="text-sm font-medium">Preparing Word document renderer...</p>
    </div>
  ),
});

interface SAPUploadProps {
  studyId: string;
  sapDocs: any[];
  tocEntries: any[];
  onRefresh: () => void;
  getAccessToken: () => Promise<string | undefined>;
  isStudyActive: boolean;
}

export function SAPUpload({
  studyId,
  sapDocs,
  tocEntries,
  onRefresh,
  getAccessToken,
  isStudyActive,
}: SAPUploadProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // SAP 预览 State
  const [previewSapDoc, setPreviewSapDoc] = useState<any>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewText, setPreviewText] = useState("");
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewBlob, setPreviewBlob] = useState<Blob | null>(null);
  const [confirmDialog, setConfirmDialog] = useState<{
    title: string;
    message: string;
    onConfirm: () => void;
  } | null>(null);

  // TOC 编辑 State
  const [editingTocEntry, setEditingTocEntry] = useState<any>(null);
  const [editForm, setEditForm] = useState({
    tlf_id: "",
    tlf_name: "",
    tlf_type: "table",
    population: "",
    analysis_type: "generic",
  });
  const [savingToc, setSavingToc] = useState(false);

  const onUploadComplete = useCallback(
    async (_objectKey: string, _filename: string) => {
      onRefresh();
    },
    [onRefresh]
  );

  const handleDeleteSap = (sapId: string) => {
    setConfirmDialog({
      title: "Delete SAP Document",
      message: "Are you sure you want to delete this SAP document? This will permanently delete the file, parsed TOC entries, and all generated reports or jobs related to it.",
      onConfirm: async () => {
        setDeletingId(sapId);
        try {
          const token = await getAccessToken();
          const res = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/sap/${sapId}`,
            {
              method: "DELETE",
              headers: { Authorization: `Bearer ${token}` },
            }
          );
          if (res.ok) {
            onRefresh();
          } else {
            const text = await res.text();
            alert(`Failed to delete SAP document: ${text}`);
          }
        } catch (err: any) {
          alert(`Error deleting SAP document: ${err.message}`);
        } finally {
          setDeletingId(null);
        }
      }
    });
  };

  const handlePreviewSap = async (doc: any) => {
    setPreviewSapDoc(doc);
    setPreviewLoading(true);
    setPreviewText("");
    setPreviewUrl(null);
    setPreviewBlob(null);

    const filename = doc.original_filename || "";
    const isPdf = filename.toLowerCase().endsWith(".pdf");
    const isDocx = filename.toLowerCase().endsWith(".docx");

    try {
      const token = await getAccessToken();
      if (isPdf || isDocx) {
        if (isPdf) {
          // 请求预签名下载 URL
          const res = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/sap/${doc.id}/download`,
            { headers: { Authorization: `Bearer ${token}` } }
          );
          if (res.ok) {
            const data = await res.json();
            setPreviewUrl(data.download_url);
          } else {
            const text = await res.text();
            alert(`Failed to fetch preview download URL: ${text}`);
          }
        } else {
          // DOCX 格式需进一步通过同源接口直接获取 Blob，避免 MinIO CORS 跨域问题
          const fileRes = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/sap/${doc.id}/file`,
            { headers: { Authorization: `Bearer ${token}` } }
          );
          if (!fileRes.ok) {
            const text = await fileRes.text();
            throw new Error(`Failed to fetch file content: ${text || fileRes.statusText}`);
          }
          const blob = await fileRes.blob();
          setPreviewBlob(blob);
        }
      } else {
        // 降级使用纯文本解析预览
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/sap/${doc.id}/preview`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (res.ok) {
          const data = await res.json();
          setPreviewText(data.parsed_text || "No parsed text available.");
        } else {
          const text = await res.text();
          alert(`Failed to fetch preview text: ${text}`);
        }
      }
    } catch (err: any) {
      alert(`Error previewing SAP: ${err.message}`);
    } finally {
      setPreviewLoading(false);
    }
  };

  const closePreview = () => {
    setPreviewSapDoc(null);
    setPreviewUrl(null);
    setPreviewBlob(null);
    setPreviewText("");
  };



  const handleEditSave = async () => {
    if (!editingTocEntry) return;
    setSavingToc(true);
    try {
      const token = await getAccessToken();
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/sap/toc/${editingTocEntry.id}`,
        {
          method: "PATCH",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(editForm),
        }
      );
      if (res.ok) {
        setEditingTocEntry(null);
        onRefresh();
      } else {
        const text = await res.text();
        alert(`Failed to save TOC entry: ${text}`);
      }
    } catch (err: any) {
      alert(`Error saving TOC entry: ${err.message}`);
    } finally {
      setSavingToc(false);
    }
  };

  const handleDeleteToc = (entryId: string) => {
    setConfirmDialog({
      title: "Delete TOC Entry",
      message: "Are you sure you want to delete this TOC entry?",
      onConfirm: async () => {
        try {
          const token = await getAccessToken();
          const res = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/sap/toc/${entryId}`,
            {
              method: "DELETE",
              headers: { Authorization: `Bearer ${token}` },
            }
          );
          if (res.ok) {
            onRefresh();
          } else {
            const text = await res.text();
            alert(`Failed to delete TOC entry: ${text}`);
          }
        } catch (err: any) {
          alert(`Error deleting TOC entry: ${err.message}`);
        }
      }
    });
  };

  const apiUploadUrl = `${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/sap/upload-file`;

  const tocTables = tocEntries.filter((e: any) => e.tlf_type === "table");
  const tocFigures = tocEntries.filter((e: any) => e.tlf_type === "figure");
  const tocListings = tocEntries.filter((e: any) => e.tlf_type === "listing");
  const generatedCount = tocEntries.filter((e: any) => e.is_generated).length;

  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">SAP Document & TOC</h2>

      {/* Uploaded SAP list */}
      {sapDocs && sapDocs.length > 0 && (
        <div className="bg-white border rounded-lg overflow-hidden shadow-sm mb-6">
          <div className="px-4 py-3 bg-gray-50 border-b font-semibold text-sm text-gray-700">
            Uploaded SAP Documents
          </div>
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b text-xs text-gray-500 uppercase">
              <tr>
                <th className="text-left px-4 py-3 font-medium">Filename</th>
                <th className="text-left px-4 py-3 font-medium">TOC Entries</th>
                <th className="text-left px-4 py-3 font-medium">Uploaded</th>
                <th className="text-right px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {sapDocs.map((doc: any) => (
                <tr key={doc.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-semibold text-gray-900">{doc.original_filename}</td>
                  <td className="px-4 py-3 text-gray-600 font-medium">
                    {doc.toc_entry_count || 0}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {doc.created_at ? new Date(doc.created_at).toLocaleString() : "-"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => handlePreviewSap(doc)}
                        className="inline-flex items-center gap-1 border border-gray-300 hover:bg-gray-50 text-gray-700 px-2.5 py-1 rounded text-xs font-semibold shadow-sm transition-all"
                      >
                        <Eye className="h-3 w-3 text-gray-500" /> Preview
                      </button>
                      <button
                        onClick={() => handleDeleteSap(doc.id)}
                        disabled={deletingId === doc.id || !isStudyActive}
                        className="inline-flex items-center gap-1 bg-red-50 hover:bg-red-100 text-red-600 px-2.5 py-1 rounded text-xs font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <Trash2 className="h-3 w-3 text-red-500" /> {deletingId === doc.id ? "..." : "Delete"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Upload section */}
      {isStudyActive ? (
        <div className="bg-white border rounded-lg p-6 mb-6">
          <h3 className="font-medium mb-3">Upload SAP Document</h3>
          <p className="text-sm text-gray-500 mb-4">
            Upload a SAP (Statistical Analysis Plan) DOCX or PDF file. The system will
            automatically extract the Table of Contents entries.
          </p>
          <FileUpload
            accept=".docx,.pdf"
            onUploadComplete={onUploadComplete}
            label="Select SAP file (.docx, .pdf)"
            apiUploadUrl={apiUploadUrl}
            getAccessToken={getAccessToken}
          />
        </div>
      ) : (
        <div className="bg-gray-100 border border-gray-200 rounded-lg p-4 mb-6 text-sm text-gray-500">
          This study is not active. Uploading SAP documents is disabled.
        </div>
      )}

      {/* TOC summary */}
      {tocEntries.length > 0 ? (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium">Table of Contents</h3>
            <span className="text-sm text-gray-500">
              {tocEntries.length} entries ({generatedCount} generated)
            </span>
          </div>

          {/* Summary cards */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-white border rounded-lg p-4">
              <div className="text-xl font-bold text-gray-800">
                {tocTables.length}
              </div>
              <div className="text-sm text-gray-500">Tables</div>
            </div>
            <div className="bg-white border rounded-lg p-4">
              <div className="text-xl font-bold text-gray-800">
                {tocFigures.length}
              </div>
              <div className="text-sm text-gray-500">Figures</div>
            </div>
            <div className="bg-white border rounded-lg p-4">
              <div className="text-xl font-bold text-gray-800">
                {tocListings.length}
              </div>
              <div className="text-sm text-gray-500">Listings</div>
            </div>
          </div>

          {/* TOC entries table */}
          <div className="bg-white border rounded-lg overflow-hidden shadow-sm">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">
                    TLF ID
                  </th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">
                    Type
                  </th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">
                    Name
                  </th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">
                    Population
                  </th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">
                    Analysis Type
                  </th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">
                    Status
                  </th>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {tocEntries.map((entry: any) => (
                  <tr key={entry.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-xs">
                      {entry.tlf_id}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                          entry.tlf_type === "table"
                            ? "bg-blue-100 text-blue-700"
                            : entry.tlf_type === "figure"
                            ? "bg-purple-100 text-purple-700"
                            : "bg-orange-100 text-orange-700"
                        }`}
                      >
                        {entry.tlf_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-700 max-w-xs truncate">
                      {entry.tlf_name || "-"}
                    </td>
                    <td className="px-4 py-3 text-gray-500">
                      {entry.population || "-"}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {entry.analysis_type || "-"}
                    </td>
                    <td className="px-4 py-3">
                      {entry.is_generated ? (
                        <span className="text-green-600 text-xs font-medium">
                          Generated
                        </span>
                      ) : (
                        <span className="text-gray-400 text-xs">Pending</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex justify-end gap-1.5">
                        <button
                          onClick={() => {
                            setEditingTocEntry(entry);
                            setEditForm({
                              tlf_id: entry.tlf_id,
                              tlf_name: entry.tlf_name || "",
                              tlf_type: entry.tlf_type || "table",
                              population: entry.population || "",
                              analysis_type: entry.analysis_type || "generic",
                            });
                          }}
                          disabled={!isStudyActive}
                          className="inline-flex items-center gap-1 border border-gray-300 hover:bg-gray-50 text-gray-700 px-2 py-1 rounded text-xs font-semibold shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <Edit2 className="h-3 w-3 text-gray-500" /> Edit
                        </button>
                        <button
                          onClick={() => handleDeleteToc(entry.id)}
                          disabled={!isStudyActive}
                          className="inline-flex items-center gap-1 bg-red-50 hover:bg-red-100 text-red-600 px-2 py-1 rounded text-xs font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <Trash2 className="h-3 w-3 text-red-500" /> Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500 text-sm">
          No SAP document uploaded yet. Upload a SAP file to extract TOC entries.
        </div>
      )}

      {/* SAP Preview Modal (Full Screen) */}
      {previewSapDoc && (
        <div className="fixed inset-0 bg-white z-50 flex flex-col animate-in fade-in duration-200">
          <div className="w-full h-full flex flex-col">
            {/* Header */}
            <div className="px-6 py-4 border-b flex justify-between items-center bg-gray-50">
              <div>
                <h3 className="font-bold text-gray-900 text-lg flex items-center gap-2">
                  <FileText className="h-5 w-5 text-blue-600" /> SAP Document Preview: {previewSapDoc.original_filename}
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  {previewUrl ? "Original PDF Preview" : previewBlob ? "Original DOCX Preview" : "Parsed Text Extract (Up to 100k characters)"}
                </p>
              </div>
              <button
                onClick={closePreview}
                className="text-gray-400 hover:text-gray-600 font-bold p-1.5 hover:bg-gray-100 rounded-lg text-sm transition-colors"
              >
                ✕
              </button>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-hidden p-6 bg-gray-100/50 flex flex-col">
              {previewLoading ? (
                <div className="flex flex-col items-center justify-center flex-1 text-gray-500 gap-3">
                  <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                  <p className="text-sm font-medium">Reading document from storage...</p>
                </div>
              ) : (
                <>
                  {previewUrl && (
                    <div className="flex-1 w-full h-full flex flex-col bg-white border rounded-lg overflow-hidden shadow-inner">
                      <iframe
                        src={previewUrl}
                        className="w-full h-full flex-1 border-0"
                        title="PDF Preview"
                      />
                    </div>
                  )}

                  {previewBlob && (
                    <DocxRenderer blob={previewBlob} />
                  )}

                  {previewText && (
                    <div className="bg-white border rounded-lg p-6 shadow-inner flex-1 overflow-auto w-full h-full">
                      <pre className="whitespace-pre-wrap font-sans text-sm text-gray-800 leading-relaxed">
                        {previewText}
                      </pre>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t bg-gray-50 flex justify-end">
              <button
                onClick={closePreview}
                className="bg-gray-950 hover:bg-gray-900 text-white px-5 py-2 rounded-lg font-semibold text-sm transition-all"
              >
                Close
              </button>
            </div>
          </div>
          {/* 内联样式修饰 docx-preview 呈现 Word 页面阴影质感 */}
          <style dangerouslySetInnerHTML={{ __html: `
            .docx-wrapper {
              background: transparent !important;
              padding: 0 !important;
              display: flex;
              flex-direction: column;
              align-items: center;
              gap: 20px;
            }
            .docx {
              box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1) !important;
              border: 1px solid #e5e7eb !important;
              background: white !important;
              max-width: 800px !important;
            }
          `}} />
        </div>
      )}

      {/* Edit TOC Entry Modal */}
      {editingTocEntry && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg flex flex-col animate-in zoom-in-95 duration-200 overflow-hidden">
            {/* Header */}
            <div className="px-6 py-4 border-b flex justify-between items-center bg-gray-50">
              <h3 className="font-bold text-gray-900 text-base">Edit Table of Contents Entry</h3>
              <button
                onClick={() => setEditingTocEntry(null)}
                className="text-gray-400 hover:text-gray-600 font-bold p-1 rounded text-sm"
              >
                ✕
              </button>
            </div>

            {/* Form Content */}
            <div className="p-6 space-y-4 text-left">
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  TLF ID
                </label>
                <input
                  type="text"
                  value={editForm.tlf_id}
                  onChange={(e) => setEditForm({ ...editForm, tlf_id: e.target.value })}
                  placeholder="e.g. Table 14.1.1.1"
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  TOC Name
                </label>
                <input
                  type="text"
                  value={editForm.tlf_name}
                  onChange={(e) => setEditForm({ ...editForm, tlf_name: e.target.value })}
                  placeholder="e.g. Summary of Subject Disposition"
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                    Type
                  </label>
                  <select
                    value={editForm.tlf_type}
                    onChange={(e) => setEditForm({ ...editForm, tlf_type: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 capitalize"
                  >
                    <option value="table">Table</option>
                    <option value="figure">Figure</option>
                    <option value="listing">Listing</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                    Population
                  </label>
                  <select
                    value={editForm.population}
                    onChange={(e) => setEditForm({ ...editForm, population: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">- Select Population -</option>
                    <option value="SS">SS (Safety Set)</option>
                    <option value="FAS">FAS (Full Analysis Set)</option>
                    <option value="PPS">PPS (Per-Protocol Set)</option>
                    <option value="ITT">ITT (Intent-to-Treat)</option>
                    <option value="Other">Other / Custom</option>
                  </select>
                  {/* 如果选了 Other，展示输入框 */}
                  {editForm.population === "Other" && (
                    <input
                      type="text"
                      placeholder="Enter custom population"
                      onChange={(e) => setEditForm({ ...editForm, population: e.target.value })}
                      className="w-full px-3 py-1.5 border rounded-lg text-xs mt-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  )}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  Analysis Type
                </label>
                <select
                  value={editForm.analysis_type}
                  onChange={(e) => setEditForm({ ...editForm, analysis_type: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="generic">Generic (通用)</option>
                  <option value="disposition">Disposition (患者处置)</option>
                  <option value="demographics">Demographics (人口学特征)</option>
                  <option value="efficacy">Efficacy (疗效分析)</option>
                  <option value="ae_summary">AE Summary (不良事件概要)</option>
                  <option value="laboratory">Laboratory (实验室检查)</option>
                  <option value="vital_signs">Vital Signs (生命体征)</option>
                </select>
              </div>
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t bg-gray-50 flex justify-end gap-3">
              <button
                onClick={() => setEditingTocEntry(null)}
                className="border border-gray-300 text-gray-700 hover:bg-gray-50 px-4 py-2 rounded-lg font-semibold text-sm transition-all"
              >
                Cancel
              </button>
              <button
                onClick={handleEditSave}
                disabled={savingToc || !editForm.tlf_id || !editForm.tlf_name}
                className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-lg font-semibold text-sm transition-all disabled:opacity-50 flex items-center gap-1.5"
              >
                {savingToc && <Loader2 className="h-4 w-4 animate-spin" />}
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {confirmDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md flex flex-col animate-in zoom-in-95 duration-200 overflow-hidden text-left animate-in fade-in">
            {/* Header */}
            <div className="px-6 py-4 border-b flex justify-between items-center bg-gray-50">
              <h3 className="font-bold text-gray-900 text-base">{confirmDialog.title}</h3>
              <button 
                onClick={() => setConfirmDialog(null)} 
                className="text-gray-400 hover:text-gray-600 font-bold p-1 hover:bg-gray-100 rounded text-sm transition-all"
              >
                ✕
              </button>
            </div>
            {/* Content */}
            <div className="p-6 text-sm text-gray-600 leading-relaxed whitespace-pre-line">
              {confirmDialog.message}
            </div>
            {/* Footer */}
            <div className="px-6 py-4 border-t bg-gray-50 flex justify-end gap-3">
              <button 
                onClick={() => setConfirmDialog(null)} 
                className="bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 px-4 py-2 rounded-lg font-semibold text-sm transition-all"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  confirmDialog.onConfirm();
                  setConfirmDialog(null);
                }}
                className="bg-red-600 hover:bg-red-700 text-white px-5 py-2 rounded-lg font-semibold text-sm transition-all"
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

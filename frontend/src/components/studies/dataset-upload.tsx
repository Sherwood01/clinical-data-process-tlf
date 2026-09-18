"use client";

import { useState, useCallback } from "react";
import { FileUpload } from "./file-upload";
import { Eye, Trash2, Loader2, Database, Table, ListChecks, Search } from "lucide-react";

interface DatasetUploadProps {
  studyId: string;
  datasets: any[];
  onRefresh: () => void;
  getAccessToken: () => Promise<string | undefined>;
  isStudyActive: boolean;
}

export function DatasetUpload({
  studyId,
  datasets,
  onRefresh,
  getAccessToken,
  isStudyActive,
}: DatasetUploadProps) {
  const [datasetName, setDatasetName] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  // 预览 State
  const [previewDataset, setPreviewDataset] = useState<any>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewData, setPreviewData] = useState<any>(null);
  const [previewTab, setPreviewTab] = useState<"data" | "variables">("data");
  const [confirmDialog, setConfirmDialog] = useState<{
    title: string;
    message: string;
    onConfirm: () => void;
  } | null>(null);

  const filteredDatasets = datasets.filter((ds) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase().trim();
    const nameMatch = ds.name ? String(ds.name).toLowerCase().includes(q) : false;
    const filenameMatch = ds.original_filename ? String(ds.original_filename).toLowerCase().includes(q) : false;
    return nameMatch || filenameMatch;
  });

  const onUploadComplete = useCallback(
    async (_objectKey: string, _filename: string) => {
      setDatasetName("");
      onRefresh();
    },
    [onRefresh]
  );

  const handlePreview = async (ds: any) => {
    setPreviewDataset(ds);
    setPreviewLoading(true);
    setPreviewTab("data");
    setPreviewData(null);
    try {
      const token = await getAccessToken();
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/datasets/${ds.id}/preview`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        setPreviewData(await res.json());
      } else {
        const text = await res.text();
        alert(`Failed to fetch preview: ${text}`);
      }
    } catch (err: any) {
      alert(`Error previewing dataset: ${err.message}`);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleDelete = (datasetId: string) => {
    setConfirmDialog({
      title: "Delete Dataset",
      message: "Are you sure you want to delete this dataset? The source file and metadata will be permanently removed.",
      onConfirm: async () => {
        setDeletingId(datasetId);
        try {
          const token = await getAccessToken();
          const res = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/datasets/${datasetId}`,
            {
              method: "DELETE",
              headers: { Authorization: `Bearer ${token}` },
            }
          );
          if (res.ok) {
            onRefresh();
          } else {
            const text = await res.text();
            alert(`Failed to delete dataset: ${text}`);
          }
        } catch (err: any) {
          alert(`Error deleting dataset: ${err.message}`);
        } finally {
          setDeletingId(null);
        }
      }
    });
  };

  const apiUploadUrl = `${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/datasets/upload-file${datasetName ? `?name=${encodeURIComponent(datasetName)}` : ""}`;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Datasets</h2>
      </div>

      {/* Upload section */}
      {isStudyActive ? (
        <div className="bg-white border rounded-lg p-6 mb-6">
          <h3 className="font-medium mb-3">Upload ADaM Dataset</h3>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Custom Upload Name (Optional)
            </label>
            <input
              type="text"
              value={datasetName}
              onChange={(e) => setDatasetName(e.target.value)}
              placeholder="Force custom name, e.g. adsl"
              className="w-full max-w-xs px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              If provided, the uploaded dataset will be named this. If left empty, it
              will be inferred from the filename. (Not recommended for multi-file upload)
            </p>
          </div>
          <FileUpload
            accept=".sas7bdat,.xpt,.csv"
            multiple={true}
            onUploadComplete={onUploadComplete}
            label="Select dataset file"
            apiUploadUrl={apiUploadUrl}
            getAccessToken={getAccessToken}
          />
        </div>
      ) : (
        <div className="bg-gray-100 border border-gray-200 rounded-lg p-4 mb-6 text-sm text-gray-500">
          This study is not active. Uploading datasets is disabled.
        </div>
      )}

      {/* Dataset list */}
      {datasets.length === 0 ? (
        <div className="text-center py-8 text-gray-500 text-sm">
          No datasets uploaded yet. Upload ADaM datasets above.
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center gap-3 max-w-xs">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search dataset..."
                className="flex h-9 w-full rounded-md border border-gray-300 bg-white px-3 py-1 text-sm shadow-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 pl-8"
              />
            </div>
          </div>

          {filteredDatasets.length === 0 ? (
            <div className="text-center py-8 text-gray-500 text-sm bg-white border rounded-lg">
              No matching datasets found.
            </div>
          ) : (
            <div className="bg-white border rounded-lg overflow-hidden shadow-sm">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">
                      Name
                    </th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">
                      Rows
                    </th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">
                      Columns
                    </th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">
                      File
                    </th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">
                      Uploaded
                    </th>
                    <th className="text-right px-4 py-3 font-medium text-gray-600">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {filteredDatasets.map((ds: any) => (
                <tr key={ds.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-semibold text-gray-900">{ds.name}</td>
                  <td className="px-4 py-3 text-gray-600 font-medium">
                    {ds.record_count?.toLocaleString() || "-"}
                  </td>
                  <td className="px-4 py-3 text-gray-600 font-medium">
                    {ds.column_count || "-"}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {ds.original_filename || "-"}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {ds.created_at
                      ? new Date(ds.created_at).toLocaleString()
                      : "-"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => handlePreview(ds)}
                        className="flex items-center gap-1 border border-gray-300 hover:bg-gray-50 text-gray-700 px-2.5 py-1 rounded text-xs font-semibold shadow-sm transition-all"
                      >
                        <Eye className="h-3 w-3 text-gray-500" /> Preview
                      </button>
                      <button
                        onClick={() => handleDelete(ds.id)}
                        disabled={deletingId === ds.id || !isStudyActive}
                        className="flex items-center gap-1 bg-red-50 hover:bg-red-100 text-red-600 px-2.5 py-1 rounded text-xs font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <Trash2 className="h-3 w-3 text-red-500" /> {deletingId === ds.id ? "..." : "Delete"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )}

      {/* Expandable Variables Detail (Optional Summary) */}
      {datasets.filter((ds: any) => ds.variables?.length > 0).length > 0 && (
        <div className="mt-8">
          <h3 className="font-semibold text-sm text-gray-700 mb-3">Dataset Variables Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {datasets
              .filter((ds: any) => ds.variables?.length > 0)
              .map((ds: any) => (
                <div key={ds.id} className="bg-white border rounded-lg overflow-hidden shadow-sm">
                  <div className="px-4 py-2 bg-gray-50 border-b font-semibold text-xs flex justify-between items-center text-gray-700">
                    <span>{ds.name.toUpperCase()} ({ds.variables.length} variables)</span>
                    <button
                      onClick={() => handlePreview(ds)}
                      className="text-blue-600 hover:underline text-[10px] font-bold"
                    >
                      View All
                    </button>
                  </div>
                  <table className="w-full text-xs text-left">
                    <tbody className="divide-y font-mono text-gray-600">
                      {(ds.variables || []).slice(0, 5).map((v: any, i: number) => (
                        <tr key={i} className="hover:bg-gray-50/50">
                          <td className="px-4 py-1.5 font-bold text-gray-900">{v.name}</td>
                          <td className="px-4 py-1.5 text-gray-500">{v.type}</td>
                          <td className="px-4 py-1.5 text-gray-700 font-sans truncate max-w-[150px]">{v.label || "-"}</td>
                        </tr>
                      ))}
                      {ds.variables.length > 5 && (
                        <tr>
                          <td
                            colSpan={3}
                            className="px-4 py-1.5 text-[10px] text-gray-400 text-center font-sans"
                          >
                            ... and {ds.variables.length - 5} more variables (click Preview to view all)
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Dataset Preview Modal */}
      {previewDataset && (
        <div className="fixed inset-0 bg-white z-50 flex flex-col animate-in fade-in duration-200">
          <div className="w-full h-full flex flex-col">
            {/* Header */}
            <div className="px-6 py-4 border-b flex justify-between items-center bg-gray-50">
              <div>
                <h3 className="font-bold text-gray-900 text-lg flex items-center gap-2">
                  <Database className="h-5 w-5 text-blue-600" /> Dataset Preview: {previewDataset.name.toUpperCase()}
                </h3>
                <p className="text-xs text-gray-500 mt-0.5 font-mono">{previewDataset.original_filename} ({previewDataset.file_format?.toUpperCase()})</p>
              </div>
              <button
                onClick={() => setPreviewDataset(null)}
                className="text-gray-400 hover:text-gray-600 font-bold p-1.5 hover:bg-gray-100 rounded-lg text-sm transition-colors"
              >
                ✕
              </button>
            </div>

            {/* Tabs */}
            <div className="px-6 border-b bg-gray-50/50 flex gap-6">
              <button
                onClick={() => setPreviewTab("data")}
                className={`py-3 text-sm font-semibold border-b-2 flex items-center gap-1.5 transition-all ${
                  previewTab === "data"
                    ? "border-blue-600 text-blue-600 font-bold"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                }`}
              >
                <Table className="h-4 w-4" /> Data Preview (First 50 rows)
              </button>
              <button
                onClick={() => setPreviewTab("variables")}
                className={`py-3 text-sm font-semibold border-b-2 flex items-center gap-1.5 transition-all ${
                  previewTab === "variables"
                    ? "border-blue-600 text-blue-600 font-bold"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                }`}
              >
                <ListChecks className="h-4 w-4" /> Variables Metadata ({previewData?.variables?.length || previewDataset.column_count || 0})
              </button>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-auto p-6 bg-gray-50/30">
              {previewLoading ? (
                <div className="flex flex-col items-center justify-center py-24 text-gray-500 gap-3">
                  <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                  <p className="text-sm font-medium">Downloading and reading dataset from storage...</p>
                </div>
              ) : previewData ? (
                <>
                  {previewTab === "data" && (
                    <div className="overflow-x-auto border rounded-lg bg-white shadow-sm max-h-[calc(100vh-220px)]">
                      <table className="w-full text-xs text-left">
                        <thead className="bg-gray-50 border-b sticky top-0 font-medium text-gray-700 z-10">
                          <tr>
                            <th className="px-3 py-2 border-r bg-gray-100/80 sticky left-0 text-center font-bold text-gray-900 w-10">#</th>
                            {previewData.columns.map((col: string) => (
                              <th key={col} className="px-3 py-2 border-r whitespace-nowrap">{col}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y font-mono text-gray-600">
                          {previewData.data.map((row: any, rIdx: number) => (
                            <tr key={rIdx} className="hover:bg-gray-50/50">
                              <td className="px-3 py-1.5 border-r bg-gray-50 text-center text-gray-400 font-sans sticky left-0 font-medium">{rIdx + 1}</td>
                              {previewData.columns.map((col: string) => (
                                <td key={col} className="px-3 py-1.5 border-r whitespace-nowrap">
                                  {row[col] === null || row[col] === undefined ? (
                                    <span className="text-gray-300 italic">null</span>
                                  ) : (
                                    String(row[col])
                                  )}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {previewTab === "variables" && (
                    <div className="border rounded-lg bg-white shadow-sm overflow-auto max-h-[calc(100vh-220px)]">
                      <table className="w-full text-sm text-left">
                        <thead className="bg-gray-50 border-b font-medium text-gray-700">
                          <tr>
                            <th className="px-4 py-2.5 font-bold">Variable Name</th>
                            <th className="px-4 py-2.5 font-bold">Type</th>
                            <th className="px-4 py-2.5 font-bold">Label</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y font-mono text-gray-600">
                          {previewData.variables?.map((v: any, vIdx: number) => (
                            <tr key={vIdx} className="hover:bg-gray-50/50">
                              <td className="px-4 py-2 text-xs font-bold text-gray-900">{v.name}</td>
                              <td className="px-4 py-2 text-xs text-gray-500">{v.type}</td>
                              <td className="px-4 py-2 text-sm text-gray-700 font-sans">{v.label || "-"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-12 text-red-500 font-medium">Failed to read dataset preview.</div>
              )}
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t bg-gray-50 flex justify-between items-center text-xs text-gray-400">
              <span>Total rows in dataset: <strong className="text-gray-700 font-semibold">{previewData?.total_rows?.toLocaleString() || previewDataset.record_count?.toLocaleString() || "-"}</strong></span>
              <button
                onClick={() => setPreviewDataset(null)}
                className="bg-gray-950 hover:bg-gray-900 text-white px-5 py-2 rounded-lg font-semibold text-sm transition-all"
              >
                Close
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


"use client";

import { useState, useCallback } from "react";
import { FileUpload } from "./file-upload";
import { Trash2 } from "lucide-react";

interface SAPUploadProps {
  studyId: string;
  sapDocs: any[];
  tocEntries: any[];
  onRefresh: () => void;
  getAccessToken: () => Promise<string | undefined>;
}

export function SAPUpload({
  studyId,
  sapDocs,
  tocEntries,
  onRefresh,
  getAccessToken,
}: SAPUploadProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const onUploadComplete = useCallback(
    async (_objectKey: string, _filename: string) => {
      onRefresh();
    },
    [onRefresh]
  );

  const handleDeleteSap = async (sapId: string) => {
    if (!window.confirm("Are you sure you want to delete this SAP document? This will permanently delete the file, parsed TOC entries, and all generated reports or jobs related to it.")) {
      return;
    }
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
                    <button
                      onClick={() => handleDeleteSap(doc.id)}
                      disabled={deletingId === doc.id}
                      className="inline-flex items-center gap-1 bg-red-50 hover:bg-red-100 text-red-600 px-2.5 py-1 rounded text-xs font-semibold transition-all disabled:opacity-50"
                    >
                      <Trash2 className="h-3 w-3 text-red-500" /> {deletingId === doc.id ? "..." : "Delete"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Upload section */}
      <div className="bg-white border rounded-lg p-6 mb-6">
        <h3 className="font-medium mb-3">Upload SAP Document</h3>
        <p className="text-sm text-gray-500 mb-4">
          Upload a SAP (Statistical Analysis Plan) DOCX file. The system will
          automatically extract the Table of Contents entries.
        </p>
        <FileUpload
          accept=".docx"
          onUploadComplete={onUploadComplete}
          label="Select SAP file (.docx)"
          apiUploadUrl={apiUploadUrl}
          getAccessToken={getAccessToken}
        />
      </div>

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
          <div className="bg-white border rounded-lg overflow-hidden">
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
    </div>
  );
}

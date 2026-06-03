"use client";

import { useState, useCallback } from "react";
import { FileUpload } from "./file-upload";

interface SAPUploadProps {
  studyId: string;
  tocEntries: any[];
  onRefresh: () => void;
  getAccessToken: () => Promise<string | null>;
}

export function SAPUpload({
  studyId,
  tocEntries,
  onRefresh,
  getAccessToken,
}: SAPUploadProps) {
  const [parsing, setParsing] = useState(false);

  const getUploadUrl = useCallback(
    async (filename: string) => {
      const token = await getAccessToken();
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/sap/upload-start`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ original_filename: filename }),
        }
      );
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    },
    [studyId, getAccessToken]
  );

  const onUploadComplete = useCallback(
    async (objectKey: string, filename: string) => {
      const token = await getAccessToken();
      setParsing(true);
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/sap/upload-complete`,
          {
            method: "POST",
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              object_key: objectKey,
              original_filename: filename,
            }),
          }
        );
        if (!res.ok) throw new Error(await res.text());
        onRefresh();
      } finally {
        setParsing(false);
      }
    },
    [studyId, getAccessToken, onRefresh]
  );

  const tocTables = tocEntries.filter((e: any) => e.tlf_type === "table");
  const tocFigures = tocEntries.filter((e: any) => e.tlf_type === "figure");
  const tocListings = tocEntries.filter((e: any) => e.tlf_type === "listing");
  const generatedCount = tocEntries.filter((e: any) => e.is_generated).length;

  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">SAP Document & TOC</h2>

      {/* Upload section */}
      <div className="bg-white border rounded-lg p-6 mb-6">
        <h3 className="font-medium mb-3">Upload SAP Document</h3>
        <p className="text-sm text-gray-500 mb-4">
          Upload a SAP (Statistical Analysis Plan) DOCX file. The system will
          automatically extract the Table of Contents entries.
        </p>
        <div className="relative">
          <FileUpload
            accept=".docx,.pdf"
            getUploadUrl={getUploadUrl}
            onUploadComplete={onUploadComplete}
            label="Select SAP file (.docx)"
          />
          {parsing && (
            <div className="mt-3 text-sm text-blue-600">
              Parsing TOC entries from SAP document...
            </div>
          )}
        </div>
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

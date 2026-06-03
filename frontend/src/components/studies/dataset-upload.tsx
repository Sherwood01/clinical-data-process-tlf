"use client";

import { useState, useCallback } from "react";
import { FileUpload } from "./file-upload";

interface DatasetUploadProps {
  studyId: string;
  datasets: any[];
  onRefresh: () => void;
  getAccessToken: () => Promise<string | null>;
}

export function DatasetUpload({
  studyId,
  datasets,
  onRefresh,
  getAccessToken,
}: DatasetUploadProps) {
  const [datasetName, setDatasetName] = useState("");

  const getUploadUrl = useCallback(
    async (filename: string) => {
      const token = await getAccessToken();
      if (!datasetName.trim()) {
        // Infer name from filename: adsl.sas7bdat → adsl
        const inferred = filename.replace(/\.sas7bdat$/i, "").toLowerCase();
        setDatasetName(inferred);
      }
      const name = datasetName.trim() || filename.replace(/\.sas7bdat$/i, "").toLowerCase();
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/datasets/upload-start`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ name }),
        }
      );
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    },
    [studyId, datasetName, getAccessToken]
  );

  const onUploadComplete = useCallback(
    async (objectKey: string, filename: string) => {
      const token = await getAccessToken();
      const name = datasetName.trim() || filename.replace(/\.sas7bdat$/i, "").toLowerCase();
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/studies/${studyId}/datasets/upload-complete`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name,
            object_key: objectKey,
            original_filename: filename,
          }),
        }
      );
      if (!res.ok) throw new Error(await res.text());
      setDatasetName("");
      onRefresh();
    },
    [studyId, datasetName, getAccessToken, onRefresh]
  );

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Datasets</h2>
      </div>

      {/* Upload section */}
      <div className="bg-white border rounded-lg p-6 mb-6">
        <h3 className="font-medium mb-3">Upload ADaM Dataset</h3>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Dataset Name
          </label>
          <input
            type="text"
            value={datasetName}
            onChange={(e) => setDatasetName(e.target.value)}
            placeholder="e.g. adsl, adae, adlb"
            className="w-full max-w-xs px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="text-xs text-gray-500 mt-1">
            Enter the dataset name (e.g., adsl, adae, adlb). If left empty, it
            will be inferred from the filename.
          </p>
        </div>
        <FileUpload
          accept=".sas7bdat,.xpt,.csv"
          getUploadUrl={getUploadUrl}
          onUploadComplete={onUploadComplete}
          label="Select .sas7bdat file"
        />
      </div>

      {/* Dataset list */}
      {datasets.length === 0 ? (
        <div className="text-center py-8 text-gray-500 text-sm">
          No datasets uploaded yet. Upload ADaM datasets above.
        </div>
      ) : (
        <div className="bg-white border rounded-lg overflow-hidden">
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
              </tr>
            </thead>
            <tbody className="divide-y">
              {datasets.map((ds: any) => (
                <tr key={ds.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{ds.name}</td>
                  <td className="px-4 py-3 text-gray-600">
                    {ds.record_count?.toLocaleString() || "-"}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {ds.column_count || "-"}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {ds.original_filename || "-"}
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {ds.created_at
                      ? new Date(ds.created_at).toLocaleString()
                      : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Variables detail - expandable */}
      {datasets.filter((ds: any) => ds.variables?.length > 0).length > 0 && (
        <div className="mt-6">
          <h3 className="font-medium mb-3">Dataset Variables</h3>
          {datasets
            .filter((ds: any) => ds.variables?.length > 0)
            .slice(0, 3)
            .map((ds: any) => (
              <div key={ds.id} className="bg-white border rounded-lg mb-3 overflow-hidden">
                <div className="px-4 py-2 bg-gray-50 border-b font-medium text-sm">
                  {ds.name} ({ds.variables.length} variables)
                </div>
                <table className="w-full text-sm">
                  <thead className="border-b">
                    <tr>
                      <th className="text-left px-4 py-2 text-gray-600 font-medium">
                        Variable
                      </th>
                      <th className="text-left px-4 py-2 text-gray-600 font-medium">
                        Type
                      </th>
                      <th className="text-left px-4 py-2 text-gray-600 font-medium">
                        Label
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {(ds.variables || []).slice(0, 10).map((v: any, i: number) => (
                      <tr key={i} className="hover:bg-gray-50">
                        <td className="px-4 py-1.5 font-mono text-xs">{v.name}</td>
                        <td className="px-4 py-1.5 text-gray-600">{v.type}</td>
                        <td className="px-4 py-1.5 text-gray-600">{v.label || "-"}</td>
                      </tr>
                    ))}
                    {ds.variables.length > 10 && (
                      <tr>
                        <td
                          colSpan={3}
                          className="px-4 py-2 text-xs text-gray-500 text-center"
                        >
                          ... and {ds.variables.length - 10} more variables
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}

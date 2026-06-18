"use client";

import { useState, useRef, useCallback } from "react";

type UploadStatus = "idle" | "requesting-url" | "uploading" | "completing" | "done" | "error";

interface FileUploadProps {
  accept: string;
  onUploadComplete: (objectKey: string, filename: string) => Promise<void>;
  getUploadUrl?: (filename: string) => Promise<{ upload_url: string; object_key: string }>;
  label: string;
  /** API proxy upload endpoint — replaces getUploadUrl two-step flow */
  apiUploadUrl?: string;
  getAccessToken?: () => Promise<string | undefined>;
}

export function FileUpload({ accept, onUploadComplete, getUploadUrl, label, apiUploadUrl, getAccessToken }: FileUploadProps) {
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(async (file: File) => {
    setError(null);
    setFileName(file.name);
    setStatus("requesting-url");

    try {
      // API proxy mode: POST file directly to backend
      if (apiUploadUrl && getAccessToken) {
        setStatus("uploading");
        const token = await getAccessToken();
        const formData = new FormData();
        formData.append("file", file);

        const res = await fetch(apiUploadUrl, {
          method: "POST",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          body: formData,
        });

        if (!res.ok) {
          const text = await res.text();
          throw new Error(text || `Upload failed: ${res.status}`);
        }

        const result = await res.json();
        setStatus("completing");
        await onUploadComplete(result.object_key || result.minio_object_key, file.name);
        setStatus("done");
        setProgress(100);
        return;
      }

      // Legacy mode: Step 1 — Request presigned URL
      if (!getUploadUrl) throw new Error("No upload method configured");
      const { upload_url, object_key } = await getUploadUrl(file.name);
      setStatus("uploading");

      // Step 2: Upload directly to MinIO via presigned URL
      const xhr = new XMLHttpRequest();
      xhr.open("PUT", upload_url, true);

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          setProgress(Math.round((e.loaded / e.total) * 100));
        }
      };

      await new Promise<void>((resolve, reject) => {
        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) resolve();
          else reject(new Error(`Upload failed: ${xhr.status}`));
        };
        xhr.onerror = () => reject(new Error("Upload failed"));
        xhr.send(file);
      });

      // Step 3: Notify API that upload is complete
      setStatus("completing");
      await onUploadComplete(object_key, file.name);

      setStatus("done");
      setProgress(100);
    } catch (err: any) {
      setError(err.message || "Upload failed");
      setStatus("error");
    }
  }, [getUploadUrl, onUploadComplete, apiUploadUrl, getAccessToken]);

  return (
    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />

      {status === "idle" && (
        <div>
          <button
            onClick={() => inputRef.current?.click()}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm"
          >
            {label}
          </button>
          <p className="text-xs text-gray-500 mt-2">Accepted: {accept}</p>
        </div>
      )}

      {(status === "requesting-url" || status === "uploading" || status === "completing") && (
        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">{fileName}</p>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {status === "requesting-url" && "Preparing upload..."}
            {status === "uploading" && `Uploading... ${progress}%`}
            {status === "completing" && "Processing..."}
          </p>
        </div>
      )}

      {status === "done" && (
        <div>
          <p className="text-sm font-medium text-green-600">Upload complete ✓</p>
          <p className="text-xs text-gray-500 mt-1">{fileName}</p>
        </div>
      )}

      {status === "error" && (
        <div>
          <p className="text-sm font-medium text-red-600">Upload failed</p>
          <p className="text-xs text-red-500 mt-1">{error}</p>
          <button
            onClick={() => {
              setStatus("idle");
              setProgress(0);
              setError(null);
            }}
            className="text-sm text-blue-600 hover:underline mt-2"
          >
            Try again
          </button>
        </div>
      )}
    </div>
  );
}

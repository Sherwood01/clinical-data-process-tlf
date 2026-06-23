"use client";

import { useState, useRef, useCallback } from "react";

type UploadStatus = "idle" | "uploading" | "done" | "error";

interface UploadItem {
  id: string;
  name: string;
  progress: number;
  status: "requesting-url" | "uploading" | "completing" | "done" | "error";
  error?: string;
}

interface FileUploadProps {
  accept: string;
  multiple?: boolean;
  onUploadComplete: (objectKey: string, filename: string) => Promise<void>;
  getUploadUrl?: (filename: string) => Promise<{ upload_url: string; object_key: string }>;
  label: string;
  /** API proxy upload endpoint — replaces getUploadUrl two-step flow */
  apiUploadUrl?: string;
  getAccessToken?: () => Promise<string | undefined>;
}

export function FileUpload({
  accept,
  multiple = false,
  onUploadComplete,
  getUploadUrl,
  label,
  apiUploadUrl,
  getAccessToken,
}: FileUploadProps) {
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [uploadingFiles, setUploadingFiles] = useState<UploadItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(
    async (files: File[]) => {
      setError(null);
      setStatus("uploading");

      // 初始化各个文件的上传进度状态
      const initialItems: UploadItem[] = files.map((file, idx) => ({
        id: `${file.name}-${idx}-${Date.now()}`,
        name: file.name,
        progress: 0,
        status: "requesting-url",
      }));
      setUploadingFiles(initialItems);

      // 并行开始所有文件的上传
      const uploadPromises = files.map(async (file, idx) => {
        const item = initialItems[idx];
        const updateItem = (updates: Partial<UploadItem>) => {
          setUploadingFiles((prev) =>
            prev.map((it) => (it.id === item.id ? { ...it, ...updates } : it))
          );
        };

        try {
          if (apiUploadUrl && getAccessToken) {
            updateItem({ status: "uploading" });
            const token = await getAccessToken();
            const formData = new FormData();
            formData.append("file", file);

            // 如果上传多个文件，剥离 query 参数 ?name=，防止重名替换覆盖
            let uploadUrl = apiUploadUrl;
            if (files.length > 1 && uploadUrl.includes("?name=")) {
              uploadUrl = uploadUrl.split("?name=")[0];
            }

            const xhr = new XMLHttpRequest();
            xhr.open("POST", uploadUrl, true);
            if (token) {
              xhr.setRequestHeader("Authorization", `Bearer ${token}`);
            }

            xhr.upload.onprogress = (e) => {
              if (e.lengthComputable) {
                updateItem({ progress: Math.round((e.loaded / e.total) * 100) });
              }
            };

            const responseText = await new Promise<string>((resolve, reject) => {
              xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                  resolve(xhr.responseText);
                } else {
                  reject(new Error(xhr.responseText || `Upload failed: ${xhr.status}`));
                }
              };
              xhr.onerror = () => reject(new Error("Upload failed"));
              xhr.send(formData);
            });

            const result = JSON.parse(responseText);
            updateItem({ status: "completing" });
            await onUploadComplete(result.object_key || result.minio_object_key, file.name);
            updateItem({ status: "done", progress: 100 });
          } else {
            // Legacy 预签名 URL 模式
            if (!getUploadUrl) throw new Error("No upload method configured");
            const { upload_url, object_key } = await getUploadUrl(file.name);
            updateItem({ status: "uploading" });

            const xhr = new XMLHttpRequest();
            xhr.open("PUT", upload_url, true);

            xhr.upload.onprogress = (e) => {
              if (e.lengthComputable) {
                updateItem({ progress: Math.round((e.loaded / e.total) * 100) });
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

            updateItem({ status: "completing" });
            await onUploadComplete(object_key, file.name);
            updateItem({ status: "done", progress: 100 });
          }
        } catch (err: any) {
          console.error(`Failed to upload file ${file.name}:`, err);
          updateItem({ status: "error", error: err.message || "Upload failed" });
          throw err;
        }
      });

      // 使用 Promise.allSettled 包装，这样即使有单个文件上传失败，其它文件也能够继续上传并渲染状态
      const results = await Promise.allSettled(uploadPromises);
      const hasErrors = results.some((r) => r.status === "rejected");

      if (hasErrors) {
        setStatus("error");
        setError("One or more files failed to upload.");
      } else {
        setStatus("done");
      }

      // 如果全部上传成功，2秒后自动恢复到空闲状态
      if (!hasErrors) {
        setTimeout(() => {
          setStatus("idle");
          setUploadingFiles([]);
        }, 2000);
      }
    },
    [getUploadUrl, onUploadComplete, apiUploadUrl, getAccessToken]
  );

  return (
    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        className="hidden"
        onChange={(e) => {
          const files = e.target.files;
          if (files && files.length > 0) handleFiles(Array.from(files));
        }}
      />

      {status === "idle" && (
        <div>
          <button
            onClick={() => inputRef.current?.click()}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm font-semibold transition-colors"
          >
            {label}
          </button>
          <p className="text-xs text-gray-500 mt-2">Accepted: {accept}</p>
        </div>
      )}

      {(status === "uploading" || status === "error" || status === "done") && uploadingFiles.length > 0 && (
        <div className="space-y-3 text-left max-h-60 overflow-y-auto p-1">
          {uploadingFiles.map((item) => (
            <div key={item.id} className="bg-gray-50 border border-gray-100 rounded-lg p-3 text-xs shadow-sm">
              <div className="flex justify-between items-center mb-1.5 font-medium">
                <span className="text-gray-700 truncate max-w-[70%]" title={item.name}>
                  {item.name}
                </span>
                <span
                  className={`font-semibold ${
                    item.status === "done"
                      ? "text-green-600"
                      : item.status === "error"
                      ? "text-red-600"
                      : "text-blue-600"
                  }`}
                >
                  {item.status === "requesting-url" && "Preparing..."}
                  {item.status === "uploading" && `Uploading... ${item.progress}%`}
                  {item.status === "completing" && "Processing..."}
                  {item.status === "done" && "Done ✓"}
                  {item.status === "error" && "Failed"}
                </span>
              </div>

              {item.status !== "done" && item.status !== "error" && (
                <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-blue-600 h-full rounded-full transition-all duration-300"
                    style={{ width: `${item.progress}%` }}
                  />
                </div>
              )}
              {item.status === "error" && item.error && (
                <p className="text-[10px] text-red-500 font-mono mt-1 break-words">
                  {item.error}
                </p>
              )}
            </div>
          ))}

          {status === "error" && (
            <div className="text-center pt-2">
              <button
                onClick={() => {
                  setStatus("idle");
                  setUploadingFiles([]);
                  setError(null);
                }}
                className="text-xs text-blue-600 hover:underline font-semibold"
              >
                Clear errors and try again
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

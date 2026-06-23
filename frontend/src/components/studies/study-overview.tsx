"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Badge } from "@/components/ui";
import { Database, FileText, FileOutput, CheckCircle2, FlaskConical, Edit2, Save, X, Trash2, AlertTriangle } from "lucide-react";

interface StudyOverviewProps {
  study: any;
  datasets: any[];
  tocEntries: any[];
  tlfJobs: any[];
  onRefresh: () => void;
  getAccessToken: () => Promise<string | undefined>;
  isStudyActive: boolean;
}

export function StudyOverview({
  study,
  datasets,
  tocEntries,
  tlfJobs,
  onRefresh,
  getAccessToken,
  isStudyActive,
}: StudyOverviewProps) {
  const router = useRouter();
  const generatedCount = tocEntries.filter((e: any) => e.is_generated).length;
  const completedJobs = tlfJobs.filter((j: any) => j.status === "completed").length;
  const failedJobs = tlfJobs.filter((j: any) => j.status === "failed").length;

  // 编辑态 State
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(study?.name || "");
  const [editProtocol, setEditProtocol] = useState(study?.protocol_id || "");
  const [editStatus, setEditStatus] = useState(study?.status || "active");
  const [editDescription, setEditDescription] = useState(study?.description || "");
  
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState<{
    title: string;
    message: string;
    onConfirm: () => void;
  } | null>(null);

  // 同步 Study 数据
  useEffect(() => {
    if (study) {
      setEditName(study.name || "");
      setEditProtocol(study.protocol_id || "");
      setEditStatus(study.status || "active");
      setEditDescription(study.description || "");
    }
  }, [study]);

  const handleSave = async () => {
    if (!editName.trim()) {
      alert("Study name is required");
      return;
    }
    setSaving(false);
    try {
      setSaving(true);
      const token = await getAccessToken();
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/studies/${study.id}`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: editName,
          protocol_id: editProtocol,
          status: editStatus,
          description: editDescription,
        }),
      });
      if (res.ok) {
        setIsEditing(false);
        onRefresh();
      } else {
        const text = await res.text();
        alert(`Failed to save: ${text}`);
      }
    } catch (err: any) {
      alert(`Error saving study: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = () => {
    setConfirmDialog({
      title: "Delete Study",
      message: "WARNING: This action is permanent! Deleting this study will delete all datasets, SAP documents, parsed TOC entries, and all generated TLF reports (both in database and in storage). Are you sure you want to proceed?",
      onConfirm: async () => {
        setDeleting(true);
        try {
          const token = await getAccessToken();
          const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/studies/${study.id}`, {
            method: "DELETE",
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });
          if (res.ok) {
            router.push("/studies");
          } else {
            const text = await res.text();
            alert(`Failed to delete study: ${text}`);
          }
        } catch (err: any) {
          alert(`Error deleting study: ${err.message}`);
        } finally {
          setDeleting(false);
        }
      }
    });
  };

  const statCards = [
    { label: "Datasets", value: datasets.length, icon: Database, color: "text-blue-600" },
    { label: "TOC Entries", value: tocEntries.length, icon: FileText, color: "text-purple-600" },
    { label: "Generated", value: generatedCount, icon: FileOutput, color: "text-emerald-600" },
    {
      label: "Jobs Completed",
      value: completedJobs,
      icon: CheckCircle2,
      color: "text-amber-600",
      extra: failedJobs > 0 ? `${failedJobs} failed` : undefined,
    },
  ];

  return (
    <div className="space-y-8">
      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.label}
              className="rounded-xl border bg-card p-5 flex items-center gap-4 shadow-sm"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                <Icon className={`h-5 w-5 ${stat.color}`} />
              </div>
              <div>
                <p className="text-2xl font-bold">{stat.value}</p>
                <p className="text-sm text-muted-foreground">{stat.label}</p>
                {stat.extra && (
                  <p className="text-xs text-destructive mt-0.5 font-medium">{stat.extra}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Study details */}
      <div className="rounded-xl border bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between border-b pb-4 mb-5">
          <div className="flex items-center gap-2">
            <FlaskConical className="h-5 w-5 text-primary" />
            <h3 className="font-semibold text-gray-900">Study Details</h3>
          </div>
          <div>
            {isEditing ? (
              <div className="flex gap-2">
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white px-3.5 py-1.5 rounded-lg text-xs font-semibold shadow-sm transition-all"
                >
                  <Save className="h-3.5 w-3.5" /> {saving ? "Saving..." : "Save"}
                </button>
                <button
                  onClick={() => setIsEditing(false)}
                  className="flex items-center gap-1.5 border border-gray-300 hover:bg-gray-50 text-gray-700 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all"
                >
                  <X className="h-3.5 w-3.5" /> Cancel
                </button>
              </div>
            ) : (
              <button
                onClick={() => setIsEditing(true)}
                className="flex items-center gap-1.5 border border-gray-300 hover:bg-gray-50 text-gray-700 px-3.5 py-1.5 rounded-lg text-xs font-semibold shadow-sm transition-all"
              >
                <Edit2 className="h-3.5 w-3.5 text-gray-500" /> Edit Details
              </button>
            )}
          </div>
        </div>

        {isEditing ? (
          <div className="space-y-4 max-w-2xl">
            <div>
              <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Study Name</label>
              <input
                type="text"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                disabled={!isStudyActive}
                className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium disabled:bg-gray-100 disabled:text-gray-500"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Protocol ID</label>
                <input
                  type="text"
                  value={editProtocol}
                  onChange={(e) => setEditProtocol(e.target.value)}
                  disabled={!isStudyActive}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium disabled:bg-gray-100 disabled:text-gray-500"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Status</label>
                <select
                  value={editStatus}
                  onChange={(e) => setEditStatus(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white font-medium"
                >
                  <option value="active">Active</option>
                  <option value="disabled">Disabled</option>
                  <option value="completed">Completed</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Description</label>
              <textarea
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                disabled={!isStudyActive}
                rows={3}
                className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
              />
            </div>
          </div>
        ) : (
          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-5 text-sm">
            <div>
              <dt className="text-muted-foreground text-xs uppercase tracking-wider mb-1">Name</dt>
              <dd className="font-semibold text-gray-900 text-base">{study?.name || "-"}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground text-xs uppercase tracking-wider mb-1">Protocol ID</dt>
              <dd className="font-semibold text-gray-900 text-base">{study?.protocol_id || "-"}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground text-xs uppercase tracking-wider mb-1">Status</dt>
              <dd className="mt-1">
                <Badge variant={study?.status === "completed" ? "default" : study?.status === "disabled" ? "destructive" : "secondary"}>
                  {study?.status || "active"}
                </Badge>
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground text-xs uppercase tracking-wider mb-1">Created</dt>
              <dd className="font-medium text-gray-700">
                {study?.created_at
                  ? new Date(study.created_at).toLocaleString()
                  : "-"}
              </dd>
            </div>
            {study?.description && (
              <div className="sm:col-span-2 pt-4 border-t mt-2">
                <dt className="text-muted-foreground text-xs uppercase tracking-wider mb-1">Description</dt>
                <dd className="text-gray-700 whitespace-pre-wrap leading-relaxed">{study.description}</dd>
              </div>
            )}
          </dl>
        )}
      </div>

      {/* Danger Zone */}
      <div className="rounded-xl border border-red-200 bg-red-50/30 p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-3 text-red-700">
          <AlertTriangle className="h-5 w-5" />
          <h3 className="font-bold text-base">Danger Zone</h3>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-gray-900">Delete this Study</p>
            <p className="text-xs text-gray-500 mt-0.5">
              Permanently remove this study, its associated datasets, SAP documents, parsed TOC entries, and all generated TLF PDF reports. This action cannot be undone.
            </p>
          </div>
          <button
            onClick={handleDelete}
            disabled={deleting || !isStudyActive}
            className="flex items-center justify-center gap-1.5 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white px-4 py-2.5 rounded-lg text-xs font-bold shadow-sm transition-all shrink-0 hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-50 disabled:hover:translate-y-0"
          >
            <Trash2 className="h-4 w-4" /> {deleting ? "Deleting Study..." : "Delete Study"}
          </button>
        </div>
      </div>

      {confirmDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md flex flex-col animate-in zoom-in-95 duration-200 overflow-hidden text-left">
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


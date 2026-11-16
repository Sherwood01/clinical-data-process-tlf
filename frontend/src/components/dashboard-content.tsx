"use client";

import { useSessionContext } from "supertokens-auth-react/recipe/session";
import { getAccessToken } from "supertokens-web-js/recipe/session";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { FlaskConical, Plus, Loader2, ArrowRight } from "lucide-react";

/**
 * 研究项目列表与管理面板组件 (遵循 Palantir Prussian Navy & Slate 规范)。
 * 提供临床研究项目的集中检索、状态跟踪与新建向导。
 *
 * @returns {React.ReactElement | null} 研究项目管理视图
 */
export default function DashboardContent() {
  const session = useSessionContext();
  const router = useRouter();
  const [studies, setStudies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newStudy, setNewStudy] = useState({ name: "", protocol_id: "", description: "" });
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (session.loading) return;
    if (!session.doesSessionExist) {
      router.push("/auth/sign-in");
      return;
    }
    fetchStudies();
  }, [session.loading, session]);

  /**
   * 从后端拉取当前租户名下的所有 Study 项目
   */
  async function fetchStudies() {
    try {
      const token = await getAccessToken();
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/studies`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        setStudies(await res.json());
      }
    } catch (err) {
      console.error("Failed to fetch studies:", err);
    } finally {
      setLoading(false);
    }
  }

  /**
   * 提交新建 Study 项目
   */
  async function handleCreateStudy() {
    if (!newStudy.name.trim()) return;
    setCreating(true);
    try {
      const token = await getAccessToken();
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/studies`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(newStudy),
        }
      );
      if (res.ok) {
        const study = await res.json();
        setShowCreate(false);
        setNewStudy({ name: "", protocol_id: "", description: "" });
        router.push(`/studies/${study.id}`);
      }
    } catch (err) {
      console.error("Failed to create study:", err);
    } finally {
      setCreating(false);
    }
  }

  if (session.loading || !session.doesSessionExist) return null;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* ── Page Header & Action Bar ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200 text-xs font-semibold mb-2 border border-slate-200 dark:border-slate-700">
            <FlaskConical className="h-3.5 w-3.5 text-[#1e3a8a] dark:text-[#93c5fd]" />
            <span>Clinical Workspace</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Studies Management
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Manage your clinical trial protocol workspaces, dataset mappings, and TLF compilation jobs.
          </p>
        </div>

        <button
          onClick={() => setShowCreate(true)}
          className="inline-flex items-center justify-center gap-2 bg-[#1e3a8a] hover:bg-[#172554] dark:bg-[#1e40af] dark:hover:bg-[#1d4ed8] text-white px-4 py-2.5 rounded-lg text-sm font-semibold shadow-xs transition-all active:scale-95 shrink-0"
        >
          <Plus className="h-4 w-4" />
          <span>New Study</span>
        </button>
      </div>

      {/* ── Study List / Empty State ── */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-24 text-slate-400 gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-[#1e3a8a] dark:text-[#93c5fd]" />
          <p className="text-sm">Loading clinical studies...</p>
        </div>
      ) : studies.length === 0 ? (
        <div className="text-center py-16 px-4 bg-white dark:bg-[#101828] border border-slate-200 dark:border-slate-800 rounded-lg shadow-xs">
          <div className="h-12 w-12 rounded-lg bg-slate-100 dark:bg-slate-800 text-[#1e3a8a] dark:text-[#93c5fd] flex items-center justify-center mx-auto mb-4 border border-slate-200 dark:border-slate-700">
            <FlaskConical className="h-6 w-6" />
          </div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-1">
            No clinical studies yet
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-6 max-w-md mx-auto">
            Create your first study project to upload ADaM datasets and generate regulatory-ready TLF reports.
          </p>
          <button
            onClick={() => setShowCreate(true)}
            className="inline-flex items-center gap-2 bg-[#1e3a8a] hover:bg-[#172554] dark:bg-[#1e40af] dark:hover:bg-[#1d4ed8] text-white px-5 py-2.5 rounded-lg text-sm font-semibold shadow-xs transition-all active:scale-95"
          >
            <Plus className="h-4 w-4" />
            <span>Create Your First Study</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {studies.map((study: any) => {
            const status = study.status || "active";
            const isCompleted = status === "completed";
            const isDisabled = status === "disabled";

            return (
              <div
                key={study.id}
                onClick={() => router.push(`/studies/${study.id}`)}
                className="group bg-white dark:bg-[#101828] border border-slate-200 dark:border-slate-800 rounded-lg p-5 hover:border-slate-300 dark:hover:border-slate-700 shadow-xs hover:shadow-sm transition-all cursor-pointer flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <h3 className="font-bold text-base text-slate-900 dark:text-slate-100 group-hover:text-[#1e3a8a] dark:group-hover:text-[#93c5fd] transition-colors leading-snug">
                      {study.name}
                    </h3>
                    <span
                      className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md shrink-0 border ${
                        isCompleted
                          ? "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800/50"
                          : isDisabled
                          ? "bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 border-rose-200 dark:border-rose-800/50"
                          : "bg-slate-100 dark:bg-slate-800 text-[#1e3a8a] dark:text-[#93c5fd] border-slate-200 dark:border-slate-700"
                      }`}
                    >
                      {status}
                    </span>
                  </div>

                  {study.protocol_id && (
                    <div className="mb-2">
                      <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                        {study.protocol_id}
                      </span>
                    </div>
                  )}

                  {study.description && (
                    <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 mt-2 leading-relaxed">
                      {study.description}
                    </p>
                  )}
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-xs text-slate-400 dark:text-slate-500">
                  <span>Open workspace</span>
                  <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#1e3a8a] dark:group-hover:text-[#93c5fd] group-hover:translate-x-0.5 transition-all" />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Create Study Modal ── */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-[#101828] border border-slate-200 dark:border-slate-800 rounded-xl p-6 w-full max-w-md shadow-2xl text-slate-900 dark:text-slate-100">
            <h2 className="text-lg font-bold mb-1 tracking-tight text-slate-900 dark:text-slate-100">
              Create New Clinical Study
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-5">
              Initialize an isolated workspace with 21 CFR Part 11 audit trails.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">
                  Study Name *
                </label>
                <input
                  type="text"
                  value={newStudy.name}
                  onChange={(e) => setNewStudy({ ...newStudy, name: e.target.value })}
                  placeholder="e.g. Phase 3 Oncology RCT"
                  className="w-full px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm bg-white dark:bg-[#0a0f1d] text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1e3a8a] dark:focus:ring-[#3b82f6]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">
                  Protocol ID
                </label>
                <input
                  type="text"
                  value={newStudy.protocol_id}
                  onChange={(e) => setNewStudy({ ...newStudy, protocol_id: e.target.value })}
                  placeholder="e.g. PROTOCOL-ABC-2026"
                  className="w-full px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm bg-white dark:bg-[#0a0f1d] text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1e3a8a] dark:focus:ring-[#3b82f6]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">
                  Description
                </label>
                <textarea
                  value={newStudy.description}
                  onChange={(e) => setNewStudy({ ...newStudy, description: e.target.value })}
                  placeholder="Brief description of trial endpoint objectives..."
                  rows={3}
                  className="w-full px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm bg-white dark:bg-[#0a0f1d] text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1e3a8a] dark:focus:ring-[#3b82f6]"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-slate-100 dark:border-slate-800">
              <button
                onClick={() => setShowCreate(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateStudy}
                disabled={!newStudy.name.trim() || creating}
                className={`px-4 py-2 rounded-lg text-xs font-semibold shadow-xs transition-all ${
                  !newStudy.name.trim() || creating
                    ? "bg-slate-200 dark:bg-slate-800 text-slate-400 cursor-not-allowed"
                    : "bg-[#1e3a8a] hover:bg-[#172554] dark:bg-[#1e40af] dark:hover:bg-[#1d4ed8] text-white active:scale-95"
                }`}
              >
                {creating ? "Creating..." : "Create Study"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

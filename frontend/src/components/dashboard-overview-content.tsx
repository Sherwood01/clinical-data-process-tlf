"use client";

import { useSessionContext } from "supertokens-auth-react/recipe/session";
import { getAccessToken } from "supertokens-web-js/recipe/session";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useUserEmail } from "@/lib/use-user-email";
import { 
  Database, 
  FileText, 
  CheckCircle, 
  XCircle, 
  Loader2, 
  FlaskConical, 
  Play, 
  Activity,
  ArrowRight,
  TrendingUp
} from "lucide-react";

export default function DashboardOverviewContent() {
  const session = useSessionContext();
  const router = useRouter();
  const { email } = useUserEmail();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (session.loading) return;
    if (!session.doesSessionExist) {
      router.push("/auth/sign-in");
      return;
    }
    fetchStats();
  }, [session.loading, session]);

  async function fetchStats() {
    try {
      const token = await getAccessToken();
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/studies/dashboard/stats`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        setStats(await res.json());
      }
    } catch (err) {
      console.error("Failed to fetch dashboard stats:", err);
    } finally {
      setLoading(false);
    }
  }

  if (session.loading) return null;
  if (!session.doesSessionExist) return null;

  const displayName = email || (!session.loading ? session.userId : "") || "User";

  // 卡片配置 (遵循 Palantir Prussian Navy & Slate 严谨数据面板规范)
  const cards = stats ? [
    { label: "Total Studies", value: stats.total_studies, icon: FlaskConical, color: "text-[#1e3a8a] dark:text-[#93c5fd]", bg: "bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700" },
    { label: "Total Datasets", value: stats.total_datasets, icon: Database, color: "text-[#1e3a8a] dark:text-[#93c5fd]", bg: "bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700" },
    { label: "TOC Entries", value: stats.total_toc, icon: FileText, color: "text-[#1e3a8a] dark:text-[#93c5fd]", bg: "bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700" },
    { label: "Total Jobs", value: stats.total_jobs, icon: Play, color: "text-amber-600 dark:text-amber-400", bg: "bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/50" },
  ] : [];

  return (
    <div className="min-h-screen bg-background text-foreground transition-colors duration-200 pb-12">
      {/* 头部欢迎条 */}
      <div className="bg-white dark:bg-[#101828] border-b border-slate-200 dark:border-slate-800 py-6 mb-8 shadow-xs">
        <div className="container mx-auto px-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200 text-xs font-semibold mb-2 border border-slate-200 dark:border-slate-700">
              <Activity className="h-3.5 w-3.5 text-[#1e3a8a] dark:text-[#93c5fd]" />
              <span>Clinical Operations Hub</span>
            </div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">Dashboard Overview</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Welcome back, <span className="font-semibold text-slate-700 dark:text-slate-300">{displayName}</span>. Real-time metrics for your clinical trial studies and TLF outputs.</p>
          </div>
          <button
            onClick={() => router.push("/studies")}
            className="flex items-center gap-2 bg-[#1e3a8a] hover:bg-[#172554] dark:bg-[#1e40af] dark:hover:bg-[#1d4ed8] text-white px-4 py-2.5 rounded-lg text-sm font-semibold shadow-xs transition-all active:scale-95"
          >
            Manage Studies <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="container mx-auto px-6 space-y-8">
        {loading ? (
          <div className="flex flex-col items-center justify-center min-h-[50vh] text-slate-400 gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-[#1e3a8a] dark:text-[#93c5fd]" />
            <p className="text-sm">Aggregating platform statistics...</p>
          </div>
        ) : (
          <>
            {/* 1. 核心指标卡片 Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {cards.map((card) => {
                const Icon = card.icon;
                return (
                  <div
                    key={card.label}
                    className="bg-white dark:bg-[#101828] border border-slate-200 dark:border-slate-800 rounded-lg p-6 shadow-xs hover:border-slate-300 dark:hover:border-slate-700 transition-all duration-200 flex items-center justify-between group"
                  >
                    <div className="space-y-1">
                      <p className="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">{card.label}</p>
                      <p className="text-3xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight">{card.value}</p>
                    </div>
                    <div className={`h-11 w-11 rounded-lg ${card.bg} flex items-center justify-center transition-transform group-hover:scale-105 duration-200 shadow-2xs`}>
                      <Icon className={`h-5 w-5 ${card.color}`} />
                    </div>
                  </div>
                );
              })}
            </div>

            {/* 2. 中层：任务状态统计 + 各研究进度 */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Study Status 状态块 */}
              <div className="bg-white dark:bg-[#101828] border border-slate-200 dark:border-slate-800 rounded-lg p-6 shadow-xs flex flex-col justify-between">
                <div>
                  <h3 className="font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2 mb-2">
                    <Activity className="h-4 w-4 text-[#1e3a8a] dark:text-[#93c5fd]" /> Study Status
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mb-6">Distribution of studies across different execution phases.</p>
                </div>
                
                <div className="space-y-4">
                  {/* Active */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600 dark:text-slate-400 flex items-center gap-1.5 font-medium">
                        <span className="h-2 w-2 rounded-full bg-[#1e3a8a] dark:bg-[#3b82f6]" /> Active
                      </span>
                      <span className="font-bold text-slate-900 dark:text-slate-100">{stats?.status_counts?.active || 0}</span>
                    </div>
                    <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div 
                        className="bg-[#1e3a8a] dark:bg-[#3b82f6] h-full rounded-full transition-all duration-500" 
                        style={{ width: `${stats?.total_studies > 0 ? ((stats?.status_counts?.active || 0) / stats.total_studies) * 100 : 0}%` }}
                      />
                    </div>
                  </div>

                  {/* Completed */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600 dark:text-slate-400 flex items-center gap-1.5 font-medium">
                        <span className="h-2 w-2 rounded-full bg-emerald-500" /> Completed
                      </span>
                      <span className="font-bold text-slate-900 dark:text-slate-100">{stats?.status_counts?.completed || 0}</span>
                    </div>
                    <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div 
                        className="bg-emerald-500 h-full rounded-full transition-all duration-500" 
                        style={{ width: `${stats?.total_studies > 0 ? ((stats?.status_counts?.completed || 0) / stats.total_studies) * 100 : 0}%` }}
                      />
                    </div>
                  </div>

                  {/* Disabled */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600 dark:text-slate-400 flex items-center gap-1.5 font-medium">
                        <span className="h-2 w-2 rounded-full bg-rose-500" /> Disabled
                      </span>
                      <span className="font-bold text-slate-900 dark:text-slate-100">{stats?.status_counts?.disabled || 0}</span>
                    </div>
                    <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div 
                        className="bg-rose-500 h-full rounded-full transition-all duration-500" 
                        style={{ width: `${stats?.total_studies > 0 ? ((stats?.status_counts?.disabled || 0) / stats.total_studies) * 100 : 0}%` }}
                      />
                    </div>
                  </div>
                </div>

                <div className="border-t border-slate-100 dark:border-slate-800/80 pt-4 mt-6 flex justify-between text-xs text-slate-400 dark:text-slate-500">
                  <span>Complete Ratio:</span>
                  <span className="font-semibold text-[#1e3a8a] dark:text-[#93c5fd]">
                    {stats?.total_studies > 0 ? `${Math.round(((stats?.status_counts?.completed || 0) / stats.total_studies) * 100)}%` : "0%"}
                  </span>
                </div>
              </div>

              {/* TLF Job 状态圆角块 */}
              <div className="bg-white dark:bg-[#101828] border border-slate-200 dark:border-slate-800 rounded-lg p-6 shadow-xs flex flex-col justify-between">
                <div>
                  <h3 className="font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2 mb-2">
                    <TrendingUp className="h-4 w-4 text-[#1e3a8a] dark:text-[#93c5fd]" /> TLF Generation Jobs
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mb-6">Realtime status distribution of report compilation tasks.</p>
                </div>
                
                <div className="space-y-4">
                  {/* Completed */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600 dark:text-slate-400 flex items-center gap-1.5 font-medium"><CheckCircle className="h-4 w-4 text-emerald-500" /> Completed</span>
                      <span className="font-bold text-slate-900 dark:text-slate-100">{stats?.job_status_counts?.completed || 0}</span>
                    </div>
                    <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div 
                        className="bg-emerald-500 h-full rounded-full transition-all duration-500" 
                        style={{ width: `${stats?.total_jobs > 0 ? ((stats?.job_status_counts?.completed || 0) / stats.total_jobs) * 100 : 0}%` }}
                      />
                    </div>
                  </div>

                  {/* Running */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600 dark:text-slate-400 flex items-center gap-1.5 font-medium"><Loader2 className="h-4 w-4 text-[#1e3a8a] dark:text-[#93c5fd] animate-spin" /> Running</span>
                      <span className="font-bold text-slate-900 dark:text-slate-100">{stats?.job_status_counts?.running || 0}</span>
                    </div>
                    <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div 
                        className="bg-[#1e3a8a] dark:bg-[#3b82f6] h-full rounded-full transition-all duration-500" 
                        style={{ width: `${stats?.total_jobs > 0 ? ((stats?.job_status_counts?.running || 0) / stats.total_jobs) * 100 : 0}%` }}
                      />
                    </div>
                  </div>

                  {/* Failed */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600 dark:text-slate-400 flex items-center gap-1.5 font-medium"><XCircle className="h-4 w-4 text-rose-500" /> Failed</span>
                      <span className="font-bold text-slate-900 dark:text-slate-100">{stats?.job_status_counts?.failed || 0}</span>
                    </div>
                    <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div 
                        className="bg-rose-500 h-full rounded-full transition-all duration-500" 
                        style={{ width: `${stats?.total_jobs > 0 ? ((stats?.job_status_counts?.failed || 0) / stats.total_jobs) * 100 : 0}%` }}
                      />
                    </div>
                  </div>

                  {/* Pending */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600 dark:text-slate-400 flex items-center gap-1.5 font-medium"><Activity className="h-4 w-4 text-slate-400" /> Pending</span>
                      <span className="font-bold text-slate-900 dark:text-slate-100">{stats?.job_status_counts?.pending || 0}</span>
                    </div>
                    <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div 
                        className="bg-slate-300 dark:bg-slate-700 h-full rounded-full transition-all duration-500" 
                        style={{ width: `${stats?.total_jobs > 0 ? ((stats?.job_status_counts?.pending || 0) / stats.total_jobs) * 100 : 0}%` }}
                      />
                    </div>
                  </div>
                </div>

                <div className="border-t border-slate-100 dark:border-slate-800/80 pt-4 mt-6 flex justify-between text-xs text-slate-400 dark:text-slate-500">
                  <span>Success Rate:</span>
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                    {stats?.total_jobs > 0 ? `${Math.round(((stats?.job_status_counts?.completed || 0) / stats.total_jobs) * 100)}%` : "0%"}
                  </span>
                </div>
              </div>

              {/* Study Progress 进度看板 */}
              <div className="bg-white dark:bg-[#101828] border border-slate-200 dark:border-slate-800 rounded-lg p-6 shadow-xs flex flex-col justify-between">
                <div>
                  <h3 className="font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2 mb-2">
                    <FlaskConical className="h-4 w-4 text-[#1e3a8a] dark:text-[#93c5fd]" /> Recent Study Progress
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mb-6">Percentage of generated table deliverables (TOC) inside each study.</p>
                </div>

                <div className="space-y-4">
                  {stats?.study_progress?.length === 0 ? (
                    <div className="text-center py-8 text-slate-400 dark:text-slate-500 text-sm">No studies available. Click "Manage Studies" to create one.</div>
                  ) : (
                    stats?.study_progress?.map((sp: any) => (
                      <div key={sp.id} className="group cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-850 p-2 rounded-lg transition-colors" onClick={() => router.push(`/studies/${sp.id}`)}>
                        <div className="flex justify-between items-center text-sm mb-1.5">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-800 dark:text-slate-200 group-hover:text-[#1e3a8a] dark:group-hover:text-[#93c5fd] transition-colors">{sp.name}</span>
                            {sp.protocol_id && <span className="text-[10px] text-slate-500 dark:text-slate-400 font-mono bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded border border-slate-200 dark:border-slate-700">{sp.protocol_id}</span>}
                          </div>
                          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">{sp.generated_toc}/{sp.total_toc} ({Math.round(sp.progress * 100)}%)</span>
                        </div>
                        <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                          <div 
                            className="bg-[#1e3a8a] dark:bg-[#3b82f6] h-full rounded-full transition-all duration-500" 
                            style={{ width: `${sp.progress * 100}%` }}
                          />
                        </div>
                      </div>
                    ))
                  )}
                </div>

                <div className="border-t border-slate-100 dark:border-slate-800/80 pt-4 mt-6 flex justify-end">
                  <button 
                    onClick={() => router.push("/studies")}
                    className="text-xs text-[#1e3a8a] dark:text-[#93c5fd] hover:text-[#172554] dark:hover:text-blue-300 font-semibold flex items-center gap-1 hover:gap-1.5 transition-all"
                  >
                    View All Studies <ArrowRight className="h-3 w-3" />
                  </button>
                </div>
              </div>
            </div>

            {/* 3. 底层：最新动态 Event Timeline */}
            <div className="bg-white dark:bg-[#101828] border border-slate-200 dark:border-slate-800 rounded-lg p-6 shadow-xs">
              <h3 className="font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2 mb-2">
                <Activity className="h-4 w-4 text-[#1e3a8a] dark:text-[#93c5fd]" /> Recent Activities
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-6 font-medium">Chronological stream of the latest TLF report compiles on the server.</p>

              <div className="flow-root">
                {stats?.recent_activities?.length === 0 ? (
                  <div className="text-center py-12 text-slate-400 dark:text-slate-500 text-sm">No recent activities on the platform yet.</div>
                ) : (
                  <ul className="-mb-8">
                    {stats?.recent_activities?.map((act: any, idx: number) => {
                      const isCompleted = act.status === "completed";
                      const isFailed = act.status === "failed";
                      const isRunning = act.status === "running";
                      
                      return (
                        <li key={act.id}>
                          <div className="relative pb-8">
                            {idx !== stats.recent_activities.length - 1 && (
                              <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-slate-200 dark:bg-slate-800" aria-hidden="true" />
                            )}
                            <div className="relative flex space-x-3 items-start">
                              <div>
                                <span className={`h-8 w-8 rounded-full flex items-center justify-center ring-4 ring-white dark:ring-[#101828] border border-slate-200 dark:border-slate-700 ${
                                  isCompleted ? "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400" :
                                  isFailed ? "bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400" :
                                  isRunning ? "bg-blue-50 dark:bg-blue-950/40 text-[#1e3a8a] dark:text-[#93c5fd]" : "bg-slate-50 dark:bg-slate-800 text-slate-400"
                                }`}>
                                  {isCompleted && <CheckCircle className="h-4 w-4" />}
                                  {isFailed && <XCircle className="h-4 w-4" />}
                                  {isRunning && <Loader2 className="h-4 w-4 animate-spin" />}
                                  {!isCompleted && !isFailed && !isRunning && <Activity className="h-4 w-4" />}
                                </span>
                              </div>
                              <div className="flex-1 min-w-0 pt-1.5 flex justify-between gap-4">
                                <div className="text-sm text-slate-500 dark:text-slate-400">
                                  <span>Generated </span>
                                  <span className="font-bold text-slate-900 dark:text-slate-100">{act.tlf_id}</span>
                                  {act.tlf_name && <span> - <span className="font-medium text-slate-700 dark:text-slate-300">{act.tlf_name}</span></span>}
                                  <span> in Study </span>
                                  <span className="font-semibold text-[#1e3a8a] dark:text-[#93c5fd] hover:underline cursor-pointer" onClick={() => router.push(`/studies/${act.study_id}`)}>{act.study_name}</span>
                                  {isFailed && <span className="text-rose-500 font-medium ml-2"> (Failed)</span>}
                                </div>
                                <div className="text-right text-xs whitespace-nowrap text-slate-400 dark:text-slate-500">
                                  {act.created_at ? new Date(act.created_at).toLocaleString() : "-"}
                                </div>
                              </div>
                            </div>
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

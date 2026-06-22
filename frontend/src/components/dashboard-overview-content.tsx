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

  // 卡片配置
  const cards = stats ? [
    { label: "Total Studies", value: stats.total_studies, icon: FlaskConical, color: "text-blue-500", bg: "bg-blue-50" },
    { label: "Total Datasets", value: stats.total_datasets, icon: Database, color: "text-purple-500", bg: "bg-purple-50" },
    { label: "TOC Entries", value: stats.total_toc, icon: FileText, color: "text-emerald-500", bg: "bg-emerald-50" },
    { label: "Total Jobs", value: stats.total_jobs, icon: Play, color: "text-amber-500", bg: "bg-amber-50" },
  ] : [];

  return (
    <div className="min-h-screen bg-gray-50/50 pb-12">
      {/* 头部欢迎条 */}
      <div className="bg-white border-b border-gray-100 py-6 mb-8 shadow-sm">
        <div className="container mx-auto px-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Dashboard Overview</h1>
            <p className="text-sm text-gray-500 mt-1">Welcome back, <span className="font-semibold text-gray-700">{displayName}</span>. Here is the statistical status of the platform.</p>
          </div>
          <button
            onClick={() => router.push("/studies")}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-lg text-sm font-semibold shadow-sm transition-all hover:-translate-y-0.5 active:translate-y-0"
          >
            Manage Studies <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="container mx-auto px-6 space-y-8">
        {loading ? (
          <div className="flex flex-col items-center justify-center min-h-[50vh] text-gray-500 gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
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
                    className="bg-white border border-gray-100/80 rounded-xl p-6 shadow-sm hover:shadow-md hover:border-gray-200/50 transition-all duration-300 flex items-center justify-between group"
                  >
                    <div className="space-y-1">
                      <p className="text-sm font-medium text-gray-400 uppercase tracking-wider">{card.label}</p>
                      <p className="text-3xl font-extrabold text-gray-900 tracking-tight">{card.value}</p>
                    </div>
                    <div className={`h-12 w-12 rounded-lg ${card.bg} flex items-center justify-center transition-transform group-hover:scale-110 duration-300`}>
                      <Icon className={`h-6 w-6 ${card.color}`} />
                    </div>
                  </div>
                );
              })}
            </div>

            {/* 2. 中层：任务状态统计 + 各研究进度 */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Study Status 状态块 */}
              <div className="bg-white border border-gray-100 rounded-xl p-6 shadow-sm flex flex-col justify-between">
                <div>
                  <h3 className="font-bold text-gray-900 flex items-center gap-2 mb-2">
                    <Activity className="h-5 w-5 text-blue-600" /> Study Status
                  </h3>
                  <p className="text-xs text-gray-500 mb-6">Distribution of studies across different execution phases.</p>
                </div>
                
                <div className="space-y-4">
                  {/* Active */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 flex items-center gap-1.5 font-medium">
                        <span className="h-2 w-2 rounded-full bg-blue-500" /> Active
                      </span>
                      <span className="font-bold text-gray-900">{stats?.status_counts?.active || 0}</span>
                    </div>
                    <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
                      <div 
                        className="bg-blue-500 h-full rounded-full transition-all duration-500" 
                        style={{ width: `${stats?.total_studies > 0 ? ((stats?.status_counts?.active || 0) / stats.total_studies) * 100 : 0}%` }}
                      />
                    </div>
                  </div>

                  {/* Completed */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 flex items-center gap-1.5 font-medium">
                        <span className="h-2 w-2 rounded-full bg-emerald-500" /> Completed
                      </span>
                      <span className="font-bold text-gray-900">{stats?.status_counts?.completed || 0}</span>
                    </div>
                    <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
                      <div 
                        className="bg-emerald-500 h-full rounded-full transition-all duration-500" 
                        style={{ width: `${stats?.total_studies > 0 ? ((stats?.status_counts?.completed || 0) / stats.total_studies) * 100 : 0}%` }}
                      />
                    </div>
                  </div>

                  {/* Disabled */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 flex items-center gap-1.5 font-medium">
                        <span className="h-2 w-2 rounded-full bg-red-500" /> Disabled
                      </span>
                      <span className="font-bold text-gray-900">{stats?.status_counts?.disabled || 0}</span>
                    </div>
                    <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
                      <div 
                        className="bg-red-500 h-full rounded-full transition-all duration-500" 
                        style={{ width: `${stats?.total_studies > 0 ? ((stats?.status_counts?.disabled || 0) / stats.total_studies) * 100 : 0}%` }}
                      />
                    </div>
                  </div>
                </div>

                <div className="border-t border-gray-100 pt-4 mt-6 flex justify-between text-xs text-gray-400">
                  <span>Active Ratio:</span>
                  <span className="font-semibold text-blue-600">
                    {stats?.total_studies > 0 ? `${Math.round(((stats?.status_counts?.active || 0) / stats.total_studies) * 100)}%` : "0%"}
                  </span>
                </div>
              </div>

              {/* TLF Job 状态圆角块 */}
              <div className="bg-white border border-gray-100 rounded-xl p-6 shadow-sm flex flex-col justify-between">
                <div>
                  <h3 className="font-bold text-gray-900 flex items-center gap-2 mb-2">
                    <TrendingUp className="h-5 w-5 text-blue-600" /> TLF Generation Jobs
                  </h3>
                  <p className="text-xs text-gray-500 mb-6">Realtime status distribution of report compilation tasks.</p>
                </div>
                
                <div className="space-y-4">
                  {/* Completed */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 flex items-center gap-1.5 font-medium"><CheckCircle className="h-4 w-4 text-emerald-500" /> Completed</span>
                      <span className="font-bold text-gray-900">{stats?.job_status_counts?.completed || 0}</span>
                    </div>
                    <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
                      <div 
                        className="bg-emerald-500 h-full rounded-full transition-all duration-500" 
                        style={{ width: `${stats?.total_jobs > 0 ? ((stats?.job_status_counts?.completed || 0) / stats.total_jobs) * 100 : 0}%` }}
                      />
                    </div>
                  </div>

                  {/* Running */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 flex items-center gap-1.5 font-medium"><Loader2 className="h-4 w-4 text-blue-500 animate-spin" /> Running</span>
                      <span className="font-bold text-gray-900">{stats?.job_status_counts?.running || 0}</span>
                    </div>
                    <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
                      <div 
                        className="bg-blue-500 h-full rounded-full transition-all duration-500" 
                        style={{ width: `${stats?.total_jobs > 0 ? ((stats?.job_status_counts?.running || 0) / stats.total_jobs) * 100 : 0}%` }}
                      />
                    </div>
                  </div>

                  {/* Failed */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 flex items-center gap-1.5 font-medium"><XCircle className="h-4 w-4 text-red-500" /> Failed</span>
                      <span className="font-bold text-gray-900">{stats?.job_status_counts?.failed || 0}</span>
                    </div>
                    <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
                      <div 
                        className="bg-red-500 h-full rounded-full transition-all duration-500" 
                        style={{ width: `${stats?.total_jobs > 0 ? ((stats?.job_status_counts?.failed || 0) / stats.total_jobs) * 100 : 0}%` }}
                      />
                    </div>
                  </div>

                  {/* Pending */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 flex items-center gap-1.5 font-medium"><Activity className="h-4 w-4 text-gray-400" /> Pending</span>
                      <span className="font-bold text-gray-900">{stats?.job_status_counts?.pending || 0}</span>
                    </div>
                    <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
                      <div 
                        className="bg-gray-400 h-full rounded-full transition-all duration-500" 
                        style={{ width: `${stats?.total_jobs > 0 ? ((stats?.job_status_counts?.pending || 0) / stats.total_jobs) * 100 : 0}%` }}
                      />
                    </div>
                  </div>
                </div>

                <div className="border-t border-gray-100 pt-4 mt-6 flex justify-between text-xs text-gray-400">
                  <span>Success Rate:</span>
                  <span className="font-semibold text-emerald-600">
                    {stats?.total_jobs > 0 ? `${Math.round(((stats?.job_status_counts?.completed || 0) / stats.total_jobs) * 100)}%` : "0%"}
                  </span>
                </div>
              </div>

              {/* Study Progress 进度看板 */}
              <div className="bg-white border border-gray-100 rounded-xl p-6 shadow-sm flex flex-col justify-between">
                <div>
                  <h3 className="font-bold text-gray-900 flex items-center gap-2 mb-2">
                    <FlaskConical className="h-5 w-5 text-blue-600" /> Recent Study Progress
                  </h3>
                  <p className="text-xs text-gray-500 mb-6">Percentage of generated table deliverables (TOC) inside each study.</p>
                </div>

                <div className="space-y-4">
                  {stats?.study_progress?.length === 0 ? (
                    <div className="text-center py-8 text-gray-400 text-sm">No studies available. Click "Manage Studies" to create one.</div>
                  ) : (
                    stats?.study_progress?.map((sp: any) => (
                      <div key={sp.id} className="group cursor-pointer hover:bg-gray-50/50 p-2 rounded-lg transition-colors" onClick={() => router.push(`/studies/${sp.id}`)}>
                        <div className="flex justify-between items-center text-sm mb-1.5">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-gray-900 group-hover:text-blue-600 transition-colors">{sp.name}</span>
                            {sp.protocol_id && <span className="text-xs text-gray-400 font-mono bg-gray-100 px-1.5 py-0.5 rounded">{sp.protocol_id}</span>}
                          </div>
                          <span className="text-xs font-semibold text-gray-600">{sp.generated_toc}/{sp.total_toc} ({Math.round(sp.progress * 100)}%)</span>
                        </div>
                        <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
                          <div 
                            className="bg-blue-600 h-full rounded-full transition-all duration-500" 
                            style={{ width: `${sp.progress * 100}%` }}
                          />
                        </div>
                      </div>
                    ))
                  )}
                </div>

                <div className="border-t border-gray-100 pt-4 mt-6 flex justify-end">
                  <button 
                    onClick={() => router.push("/studies")}
                    className="text-xs text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1 hover:gap-1.5 transition-all"
                  >
                    View All Studies <ArrowRight className="h-3 w-3" />
                  </button>
                </div>
              </div>
            </div>

            {/* 3. 底层：最新动态 Event Timeline */}
            <div className="bg-white border border-gray-100 rounded-xl p-6 shadow-sm">
              <h3 className="font-bold text-gray-900 flex items-center gap-2 mb-2">
                <Activity className="h-5 w-5 text-blue-600" /> Recent Activities
              </h3>
              <p className="text-xs text-gray-500 mb-6 font-medium">Chronological stream of the latest TLF report compiles on the server.</p>

              <div className="flow-root">
                {stats?.recent_activities?.length === 0 ? (
                  <div className="text-center py-12 text-gray-400 text-sm">No recent activities on the platform yet.</div>
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
                              <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-100" aria-hidden="true" />
                            )}
                            <div className="relative flex space-x-3 items-start">
                              <div>
                                <span className={`h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white ${
                                  isCompleted ? "bg-emerald-50 text-emerald-600" :
                                  isFailed ? "bg-red-50 text-red-600" :
                                  isRunning ? "bg-blue-50 text-blue-600" : "bg-gray-50 text-gray-400"
                                }`}>
                                  {isCompleted && <CheckCircle className="h-4 w-4" />}
                                  {isFailed && <XCircle className="h-4 w-4" />}
                                  {isRunning && <Loader2 className="h-4 w-4 animate-spin" />}
                                  {!isCompleted && !isFailed && !isRunning && <Activity className="h-4 w-4" />}
                                </span>
                              </div>
                              <div className="flex-1 min-w-0 pt-1.5 flex justify-between gap-4">
                                <div className="text-sm text-gray-500">
                                  <span>Generated </span>
                                  <span className="font-bold text-gray-900">{act.tlf_id}</span>
                                  {act.tlf_name && <span> - <span className="font-medium text-gray-600">{act.tlf_name}</span></span>}
                                  <span> in Study </span>
                                  <span className="font-semibold text-blue-600 hover:underline cursor-pointer" onClick={() => router.push(`/studies/${act.study_id}`)}>{act.study_name}</span>
                                  {isFailed && <span className="text-red-500 font-medium ml-2"> (Failed)</span>}
                                </div>
                                <div className="text-right text-xs whitespace-nowrap text-gray-400">
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

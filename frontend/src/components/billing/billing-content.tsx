"use client";

import { useSessionContext } from "supertokens-auth-react/recipe/session";
import { getAccessToken } from "supertokens-web-js/recipe/session";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useUserEmail } from "@/lib/use-user-email";
import { 
  CreditCard, 
  Check, 
  HelpCircle, 
  ArrowRight, 
  Users, 
  Shield, 
  Zap, 
  Sparkles, 
  Layers, 
  ExternalLink,
  Loader2,
  FileText,
  FlaskConical
} from "lucide-react";

// 定义 Creem 产品（Product）默认常量，若无环境变量则使用此默认值
const DEFAULT_PRODUCT_PRO = "prod_pro_test"; // 个人专业版
const DEFAULT_PRODUCT_PLUS = "prod_plus_test"; // 团队协作版

interface PlanDetail {
  plan_type: string;
  subscription_status: string | null;
  current_period_end: string | null;
  monthly_usage_count: number;
  max_studies: number;
  max_tlfs: number;
  billing_portal_url?: string | null;
}

interface BillingStatus {
  tenant: PlanDetail;
  user: PlanDetail;
}

/**
 * 计费及订阅管理页面组件。
 * 提供当前配额用量可视化仪表盘，及 Pro、Plus、Enterprise 等四层级方案对比升级入口。
 */
export default function BillingContent() {
  const session = useSessionContext();
  const router = useRouter();
  const { email } = useUserEmail();
  
  const [status, setStatus] = useState<BillingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null); // 记录哪个 plan 正在发起 checkout
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // 挂载时校验登录并拉取计费状态数据
  useEffect(() => {
    if (session.loading) return;
    if (!session.doesSessionExist) {
      router.push("/auth/sign-in");
      return;
    }
    fetchBillingStatus();
  }, [session.loading, session]);

  /**
   * 从后端拉取最新的租户与用户订阅计划及配额使用情况。
   */
  const fetchBillingStatus = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      const token = await getAccessToken();
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "";
      const res = await fetch(`${apiUrl}/billing/status`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) {
        throw new Error(`获取订阅状态失败: ${res.status}`);
      }

      const data = await res.json();
      setStatus(data);
    } catch (err: any) {
      console.error(err);
      setErrorMsg("无法加载订阅计费数据，请稍后刷新重试。");
    } finally {
      setLoading(false);
    }
  };

  /**
   * 申请 Creem 收银台链接并跳转到支付页面。
   * 
   * @param planType 期望升级的订阅类型 ('pro' | 'plus')
   * @param variantId Creem 产品 ID
   */
  const handleUpgrade = async (planType: "pro" | "plus", variantId: string) => {
    try {
      setCheckoutLoading(planType);
      setErrorMsg(null);
      const token = await getAccessToken();
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "";
      
      // 使用 window.location.origin 拼接支付成功后的回显地址
      const redirectUrl = `${window.location.origin}/billing`;

      const res = await fetch(`${apiUrl}/billing/checkout`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          variant_id: variantId,
          plan_type: planType,
          redirect_url: redirectUrl,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `发起升级失败: ${res.status}`);
      }

      const data = await res.json();
      if (data.checkout_url) {
        // 重定向至 Creem 官方安全收银台
        window.location.href = data.checkout_url;
      } else {
        throw new Error("后端未返回收银台支付链接");
      }
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || "发起支付失败，请检查网络或联系客服人员。");
    } finally {
      setCheckoutLoading(null);
    }
  };

  if (session.loading || loading) {
    return (
      <div className="min-h-[80vh] flex flex-col items-center justify-center text-slate-400 gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-[#1e3a8a] dark:text-[#93c5fd]" />
        <p className="text-sm">Loading subscription billing data...</p>
      </div>
    );
  }

  if (errorMsg) {
    return (
      <div className="min-h-[80vh] flex flex-col items-center justify-center gap-4 text-center px-4">
        <p className="text-rose-500 font-semibold">{errorMsg}</p>
        <button
          onClick={fetchBillingStatus}
          className="bg-[#1e3a8a] hover:bg-[#172554] dark:bg-[#1e40af] dark:hover:bg-[#1d4ed8] text-white px-4 py-2 rounded-lg text-sm shadow-xs transition-all"
        >
          Reload
        </button>
      </div>
    );
  }

  // 提取当前用户的账单管理入口
  const portalUrl = status?.tenant.billing_portal_url || null;
  const currentTenantPlan = status?.tenant.plan_type || "free";
  const currentUserPlan = status?.user.plan_type || "free";

  // 读取配置的 Creem 产品 ID，如果未在环境变量中配置，使用沙箱默认值
  const variantPro = process.env.NEXT_PUBLIC_CREEM_PRODUCT_ID_PRO || DEFAULT_PRODUCT_PRO;
  const variantPlus = process.env.NEXT_PUBLIC_CREEM_PRODUCT_ID_PLUS || DEFAULT_PRODUCT_PLUS;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#0a0f1d] text-slate-900 dark:text-slate-100 pb-16 transition-colors">
      {/* 头部区域 */}
      <div className="bg-white dark:bg-[#101828] border-b border-slate-200 dark:border-slate-800 py-8 mb-8 shadow-xs transition-colors">
        <div className="container mx-auto px-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div>
            <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight flex items-center gap-2">
              <Layers className="h-7 w-7 text-[#1e3a8a] dark:text-[#93c5fd]" />
              Plans & Billing Center
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
              Manage subscription tiers, monitor workspace quotas, or upgrade your team to unlock advanced collaboration features.
            </p>
          </div>
          {portalUrl && (
            <a
              href={portalUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 bg-[#1e3a8a] hover:bg-[#172554] dark:bg-[#1e40af] dark:hover:bg-[#1d4ed8] text-white px-5 py-3 rounded-lg text-sm font-semibold shadow-xs transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0"
            >
              <CreditCard className="h-4 w-4" />
              Manage Billing & Subscriptions
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          )}
        </div>
      </div>

      <div className="container mx-auto px-6 space-y-8">
        {/* 用量限制仪表盘 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 个人套餐额度卡片 */}
          <div className="bg-white dark:bg-[#101828] border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-xs flex flex-col justify-between transition-colors">
            <div>
              <div className="flex justify-between items-center mb-6">
                <div>
                  <span className="text-xs font-semibold uppercase tracking-wider text-[#1e3a8a] dark:text-[#93c5fd]">
                    Personal Plan Quota
                  </span>
                  <h3 className="text-xl font-bold mt-1 text-slate-900 dark:text-white capitalize">
                    {currentUserPlan === "pro" ? "Pro Plan" : "Free Plan"}
                  </h3>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-slate-100 dark:bg-slate-800 text-[#1e3a8a] dark:text-[#93c5fd] border border-slate-200 dark:border-slate-700">
                  {currentUserPlan === "pro" ? "Active" : "Default"}
                </span>
              </div>

              {/* 用量条 1: Study 项目创建数 */}
              <div className="space-y-2 mb-6">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600 dark:text-slate-400 flex items-center gap-1.5">
                    <FlaskConical className="h-4 w-4" />
                    Created Study Projects
                  </span>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {status?.user.monthly_usage_count ?? 0} / {status?.user.max_studies === 999999 ? "Unlimited" : status?.user.max_studies}
                  </span>
                </div>
                <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-[#1e3a8a] dark:bg-[#3b82f6] h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${Math.min(
                        ((status?.user.monthly_usage_count ?? 0) / (status?.user.max_studies || 1)) * 100,
                        100
                      )}%`,
                    }}
                  />
                </div>
              </div>

              {/* 用量条 2: TLF 报告生成数 */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600 dark:text-slate-400 flex items-center gap-1.5">
                    <FileText className="h-4 w-4" />
                    TLF Generates (This Month)
                  </span>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {status?.user.monthly_usage_count ?? 0} / {status?.user.max_tlfs === 999999 ? "Unlimited" : status?.user.max_tlfs}
                  </span>
                </div>
                <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-emerald-500 dark:bg-emerald-400 h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${Math.min(
                        ((status?.user.monthly_usage_count ?? 0) / (status?.user.max_tlfs || 1)) * 100,
                        100
                      )}%`,
                    }}
                  />
                </div>
              </div>
            </div>

            {status?.user.current_period_end && (
              <p className="text-xs text-slate-400 dark:text-slate-500 mt-6">
                Current period ends: {new Date(status.user.current_period_end).toLocaleDateString("en-US")} (Quotas reset monthly)
              </p>
            )}
          </div>

          {/* 团队/租户空间套餐额度卡片 */}
          <div className="bg-white dark:bg-[#101828] border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-xs flex flex-col justify-between transition-colors">
            <div>
              <div className="flex justify-between items-center mb-6">
                <div>
                  <span className="text-xs font-semibold uppercase tracking-wider text-amber-600 dark:text-amber-400">
                    Team Space Quota (Tenant)
                  </span>
                  <h3 className="text-xl font-bold mt-1 text-slate-900 dark:text-white capitalize">
                    {currentTenantPlan === "plus"
                      ? "Plus Plan"
                      : currentTenantPlan === "enterprise"
                      ? "Enterprise Plan"
                      : "Free Plan"}
                  </h3>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800/60">
                  {currentTenantPlan !== "free" ? "Active" : "Default"}
                </span>
              </div>

              {/* 用量条 1: Study 项目创建数 */}
              <div className="space-y-2 mb-6">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600 dark:text-slate-400 flex items-center gap-1.5">
                    <FlaskConical className="h-4 w-4" />
                    Created Study Projects
                  </span>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {status?.tenant.monthly_usage_count ?? 0} / {status?.tenant.max_studies === 999999 ? "Unlimited" : status?.tenant.max_studies}
                  </span>
                </div>
                <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-amber-500 dark:bg-amber-400 h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${Math.min(
                        ((status?.tenant.monthly_usage_count ?? 0) / (status?.tenant.max_studies || 1)) * 100,
                        100
                      )}%`,
                    }}
                  />
                </div>
              </div>

              {/* 用量条 2: TLF 报告生成数 */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600 dark:text-slate-400 flex items-center gap-1.5">
                    <FileText className="h-4 w-4" />
                    Team TLF Generates (This Month)
                  </span>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {status?.tenant.monthly_usage_count ?? 0} / {status?.tenant.max_tlfs === 999999 ? "Unlimited" : status?.tenant.max_tlfs}
                  </span>
                </div>
                <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-emerald-500 dark:bg-emerald-400 h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${Math.min(
                        ((status?.tenant.monthly_usage_count ?? 0) / (status?.tenant.max_tlfs || 1)) * 100,
                        100
                      )}%`,
                    }}
                  />
                </div>
              </div>
            </div>

            {status?.tenant.current_period_end && (
              <p className="text-xs text-slate-400 dark:text-slate-500 mt-6">
                Tenant billing period ends: {new Date(status.tenant.current_period_end).toLocaleDateString("en-US")} (Quotas reset monthly)
              </p>
            )}
          </div>
        </div>

        {/* 四层级方案定价网格 */}
        <div>
          <div className="text-center max-w-xl mx-auto mb-10">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Choose a Plan to Fit Your Needs</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
              Whether you are an independent programmer or a clinical biostatistics team, we have custom tiers and SLA support for you.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 items-stretch">
            {/* Plan 1: Free */}
            <div className="bg-white dark:bg-[#101828] border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-xs flex flex-col justify-between hover:border-slate-300 dark:hover:border-slate-700 transition-all">
              <div>
                <h4 className="text-lg font-bold text-slate-900 dark:text-white">Free Plan</h4>
                <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">Ideal for evaluating the platform and initial trial</p>
                <div className="my-6">
                  <span className="text-3xl font-extrabold text-slate-900 dark:text-white">$0</span>
                  <span className="text-slate-400 dark:text-slate-500 text-sm font-medium"> / Forever</span>
                </div>
                <hr className="border-slate-100 dark:border-slate-800 my-4" />
                <ul className="space-y-3 text-sm text-slate-600 dark:text-slate-400">
                  <li className="flex items-start gap-2.5">
                    <Check className="h-4.5 w-4.5 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <span>Up to 1 Study project</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <Check className="h-4.5 w-4.5 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <span>Up to 10 TLF generation runs / month</span>
                  </li>
                  <li className="flex items-start gap-2.5 text-slate-300 dark:text-slate-700">
                    <Check className="h-4.5 w-4.5 text-slate-300 dark:text-slate-700 flex-shrink-0 mt-0.5" />
                    <span>No collaborative team workspaces</span>
                  </li>
                  <li className="flex items-start gap-2.5 text-slate-300 dark:text-slate-700">
                    <Check className="h-4.5 w-4.5 text-slate-300 dark:text-slate-700 flex-shrink-0 mt-0.5" />
                    <span>No AI-powered SAP error correction</span>
                  </li>
                </ul>
              </div>
              <div className="mt-8">
                <button
                  disabled
                  className="w-full bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-500 border border-slate-200 dark:border-slate-700 py-2.5 rounded-lg text-sm font-bold cursor-not-allowed"
                >
                  {currentUserPlan === "free" && currentTenantPlan === "free" ? "Default" : "Basic Free"}
                </button>
              </div>
            </div>

            {/* Plan 2: Pro */}
            <div className="bg-white dark:bg-[#101828] border-2 border-[#1e3a8a] dark:border-[#3b82f6] rounded-xl p-6 shadow-sm flex flex-col justify-between relative transition-all">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#1e3a8a] dark:bg-[#1e40af] text-white text-[10px] uppercase font-bold tracking-wider px-3 py-0.5 rounded-full shadow-xs">
                Recommended
              </div>
              <div>
                <h4 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                  Pro Plan
                  <Zap className="h-4 w-4 text-[#1e3a8a] dark:text-[#93c5fd]" />
                </h4>
                <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">Recommended for independent biostatisticians and clinical programmers</p>
                <div className="my-6">
                  <span className="text-3xl font-extrabold text-slate-900 dark:text-white">$29</span>
                  <span className="text-slate-400 dark:text-slate-500 text-sm font-medium"> / Month</span>
                </div>
                <hr className="border-slate-100 dark:border-slate-800 my-4" />
                <ul className="space-y-3 text-sm text-slate-600 dark:text-slate-400">
                  <li className="flex items-start gap-2.5">
                    <Check className="h-4.5 w-4.5 text-[#1e3a8a] dark:text-[#93c5fd] flex-shrink-0 mt-0.5" />
                    <span>Up to 50 Study projects</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <Check className="h-4.5 w-4.5 text-[#1e3a8a] dark:text-[#93c5fd] flex-shrink-0 mt-0.5" />
                    <span>Up to 500 TLF generation runs / month</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <Check className="h-4.5 w-4.5 text-[#1e3a8a] dark:text-[#93c5fd] flex-shrink-0 mt-0.5" />
                    <span>Full access to Figures & SAP parsing</span>
                  </li>
                  <li className="flex items-start gap-2.5 text-slate-300 dark:text-slate-700">
                    <Check className="h-4.5 w-4.5 text-slate-300 dark:text-slate-700 flex-shrink-0 mt-0.5" />
                    <span>Strictly for single-user workspaces</span>
                  </li>
                </ul>
              </div>
              <div className="mt-8">
                {currentUserPlan === "pro" ? (
                  <button
                    disabled
                    className="w-full bg-slate-100 dark:bg-slate-800 text-[#1e3a8a] dark:text-[#93c5fd] border border-slate-200 dark:border-slate-700 py-2.5 rounded-lg text-sm font-bold"
                  >
                    Active (Personal Pro)
                  </button>
                ) : (
                  <button
                    onClick={() => handleUpgrade("pro", variantPro)}
                    disabled={checkoutLoading !== null}
                    className="w-full bg-[#1e3a8a] hover:bg-[#172554] dark:bg-[#1e40af] dark:hover:bg-[#1d4ed8] active:scale-[0.98] text-white py-2.5 rounded-lg text-sm font-bold shadow-xs transition-all flex items-center justify-center gap-1.5"
                  >
                    {checkoutLoading === "pro" ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Redirecting to checkout...
                      </>
                    ) : (
                      <>
                        Upgrade Now
                        <ArrowRight className="h-4 w-4" />
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>

            {/* Plan 3: Plus */}
            <div className="bg-white dark:bg-[#101828] border border-slate-200 dark:border-slate-800 hover:border-amber-500/60 dark:hover:border-amber-500/60 rounded-xl p-6 shadow-xs flex flex-col justify-between hover:shadow-sm transition-all relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-amber-600 dark:bg-amber-500 text-white text-[10px] uppercase font-bold tracking-wider px-3 py-0.5 rounded-full shadow-xs">
                For Teams
              </div>
              <div>
                <h4 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                  Plus Plan
                  <Sparkles className="h-4 w-4 text-amber-500" />
                </h4>
                <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">Best for clinical trial groups and CRO departments</p>
                <div className="my-6">
                  <span className="text-3xl font-extrabold text-slate-900 dark:text-white">$99</span>
                  <span className="text-slate-400 dark:text-slate-500 text-sm font-medium"> / Month</span>
                </div>
                <hr className="border-slate-100 dark:border-slate-800 my-4" />
                <ul className="space-y-3 text-sm text-slate-600 dark:text-slate-400">
                  <li className="flex items-start gap-2.5">
                    <Check className="h-4.5 w-4.5 text-amber-500 flex-shrink-0 mt-0.5" />
                    <span>Up to 200 Study projects</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <Check className="h-4.5 w-4.5 text-amber-500 flex-shrink-0 mt-0.5" />
                    <span>Up to 5000 shared TLF runs / month</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <Check className="h-4.5 w-4.5 text-amber-500 flex-shrink-0 mt-0.5" />
                    <span>Collaborative workspaces up to 10 members</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <Check className="h-4.5 w-4.5 text-amber-500 flex-shrink-0 mt-0.5" />
                    <span>AI corrections & DOCX format export unlocked</span>
                  </li>
                </ul>
              </div>
              <div className="mt-8">
                {currentTenantPlan === "plus" ? (
                  <button
                    disabled
                    className="w-full bg-amber-50 dark:bg-amber-950/20 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-900/50 py-2.5 rounded-lg text-sm font-bold"
                  >
                    Active (Tenant Plus)
                  </button>
                ) : (
                  <button
                    onClick={() => handleUpgrade("plus", variantPlus)}
                    disabled={checkoutLoading !== null}
                    className="w-full bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:hover:bg-white text-white dark:text-slate-900 active:scale-[0.98] py-2.5 rounded-lg text-sm font-bold shadow-xs transition-all flex items-center justify-center gap-1.5"
                  >
                    {checkoutLoading === "plus" ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Redirecting to checkout...
                      </>
                    ) : (
                      <>
                        Upgrade Team
                        <ArrowRight className="h-4 w-4" />
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>

            {/* Plan 4: Enterprise */}
            <div className="bg-white dark:bg-[#101828] border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-xs flex flex-col justify-between hover:border-slate-300 dark:hover:border-slate-700 transition-all">
              <div>
                <h4 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                  Enterprise Plan
                  <Shield className="h-4 w-4 text-emerald-500" />
                </h4>
                <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">Dedicated deployment for large CROs & biotechs</p>
                <div className="my-6">
                  <span className="text-3xl font-extrabold text-slate-900 dark:text-white">Custom</span>
                  <span className="text-slate-400 dark:text-slate-500 text-sm font-medium"> / Annual</span>
                </div>
                <hr className="border-slate-100 dark:border-slate-800 my-4" />
                <ul className="space-y-3 text-sm text-slate-600 dark:text-slate-400">
                  <li className="flex items-start gap-2.5">
                    <Check className="h-4.5 w-4.5 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <span>Unlimited Studies & collaborators</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <Check className="h-4.5 w-4.5 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <span>Unlimited TLF generation runs</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <Check className="h-4.5 w-4.5 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <span>Dedicated physical / logical isolation</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <Check className="h-4.5 w-4.5 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <span>Enterprise SLA & custom Figures support</span>
                  </li>
                </ul>
              </div>
              <div className="mt-8">
                {currentTenantPlan === "enterprise" ? (
                  <button
                    disabled
                    className="w-full bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-900/50 py-2.5 rounded-lg text-sm font-bold"
                  >
                    Active (Enterprise)
                  </button>
                ) : (
                  <a
                    href="mailto:info@xwqin.com?subject=Clinical Trial TLF Generator Enterprise Inquiry"
                    className="w-full bg-slate-900 hover:bg-slate-800 text-white dark:bg-slate-100 dark:hover:bg-white dark:text-slate-900 py-2.5 rounded-lg text-sm font-bold shadow-xs transition-all flex items-center justify-center gap-1.5"
                  >
                    Contact Sales
                    <Users className="h-4 w-4" />
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* 常见问题说明 */}
        <div className="bg-white dark:bg-[#101828] border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-xs max-w-4xl mx-auto transition-colors">
          <h3 className="text-xl font-bold mb-6 text-slate-900 dark:text-white flex items-center gap-2">
            <HelpCircle className="h-5.5 w-5.5 text-[#1e3a8a] dark:text-[#93c5fd]" />
            Frequently Asked Questions about Billing
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-slate-600 dark:text-slate-400">
            <div>
              <h5 className="font-semibold text-slate-900 dark:text-white">Do Personal Pro and Team Plus conflict?</h5>
              <p className="mt-1 text-xs leading-relaxed">
                No. If a workspace is upgraded to Plus (Team), all collaborators automatically inherit the Plus quotas and features without needing individual Pro plans. If the workspace is on the Free tier, individual Pro subscribers still access advanced features within their workspaces.
              </p>
            </div>
            <div>
              <h5 className="font-semibold text-slate-900 dark:text-white">How do I manage refunds, payment methods, or cancellations?</h5>
              <p className="mt-1 text-xs leading-relaxed">
                All transactions are managed securely by Creem. If you have an active plan, a &apos;Manage Billing&apos; button will appear at the top. Click it to download invoices, cancel subscriptions (active until the billing period ends), or update your payment card information.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


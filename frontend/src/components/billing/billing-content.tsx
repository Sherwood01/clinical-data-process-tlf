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
      <div className="min-h-[80vh] flex flex-col items-center justify-center text-gray-500 dark:text-gray-400 gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600 dark:text-blue-400" />
        <p className="text-sm">Loading subscription billing data...</p>
      </div>
    );
  }

  if (errorMsg) {
    return (
      <div className="min-h-[80vh] flex flex-col items-center justify-center gap-4 text-center px-4">
        <p className="text-red-500 font-semibold">{errorMsg}</p>
        <button
          onClick={fetchBillingStatus}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm transition-all"
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
    <div className="min-h-screen bg-gray-50/30 dark:bg-gray-900/10 pb-16">
      {/* 头部区域 */}
      <div className="bg-white dark:bg-gray-950 border-b border-gray-100 dark:border-gray-800 py-8 mb-8 shadow-sm">
        <div className="container mx-auto px-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div>
            <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight flex items-center gap-2">
              <Layers className="h-7 w-7 text-indigo-600 dark:text-indigo-400 animate-pulse" />
              Plans & Billing Center
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
              Manage subscription tiers, monitor workspace quotas, or upgrade your team to unlock advanced collaboration features.
            </p>
          </div>
          {portalUrl && (
            <a
              href={portalUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-3 rounded-xl text-sm font-semibold shadow-md transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0"
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
          <div className="bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-center mb-6">
                <div>
                  <span className="text-xs font-semibold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
                    Personal Plan Quota
                  </span>
                  <h3 className="text-xl font-bold mt-1 text-gray-900 dark:text-white capitalize">
                    {currentUserPlan === "pro" ? "Pro Plan" : "Free Plan"}
                  </h3>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400">
                  {currentUserPlan === "pro" ? "Active" : "Default"}
                </span>
              </div>

              {/* 用量条 1: Study 项目创建数 */}
              <div className="space-y-2 mb-6">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1.5">
                    <FlaskConical className="h-4 w-4" />
                    Created Study Projects
                  </span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {status?.user.monthly_usage_count ?? 0} / {status?.user.max_studies === 999999 ? "Unlimited" : status?.user.max_studies}
                  </span>
                </div>
                <div className="w-full bg-gray-100 dark:bg-gray-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-indigo-600 dark:bg-indigo-400 h-full rounded-full transition-all duration-500"
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
                  <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1.5">
                    <FileText className="h-4 w-4" />
                    TLF Generates (This Month)
                  </span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {status?.user.monthly_usage_count ?? 0} / {status?.user.max_tlfs === 999999 ? "Unlimited" : status?.user.max_tlfs}
                  </span>
                </div>
                <div className="w-full bg-gray-100 dark:bg-gray-800 h-2 rounded-full overflow-hidden">
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
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-6">
                Current period ends: {new Date(status.user.current_period_end).toLocaleDateString("en-US")} (Quotas reset monthly)
              </p>
            )}
          </div>

          {/* 团队/租户空间套餐额度卡片 */}
          <div className="bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-center mb-6">
                <div>
                  <span className="text-xs font-semibold uppercase tracking-wider text-violet-600 dark:text-violet-400">
                    Team Space Quota (Tenant)
                  </span>
                  <h3 className="text-xl font-bold mt-1 text-gray-900 dark:text-white capitalize">
                    {currentTenantPlan === "plus"
                      ? "Plus Plan"
                      : currentTenantPlan === "enterprise"
                      ? "Enterprise Plan"
                      : "Free Plan"}
                  </h3>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-violet-50 dark:bg-violet-950/50 text-violet-600 dark:text-violet-400">
                  {currentTenantPlan !== "free" ? "Active" : "Default"}
                </span>
              </div>

              {/* 用量条 1: Study 项目创建数 */}
              <div className="space-y-2 mb-6">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1.5">
                    <FlaskConical className="h-4 w-4" />
                    Created Study Projects
                  </span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {status?.tenant.monthly_usage_count ?? 0} / {status?.tenant.max_studies === 999999 ? "Unlimited" : status?.tenant.max_studies}
                  </span>
                </div>
                <div className="w-full bg-gray-100 dark:bg-gray-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-violet-600 dark:bg-violet-400 h-full rounded-full transition-all duration-500"
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
                  <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1.5">
                    <FileText className="h-4 w-4" />
                    Team TLF Generates (This Month)
                  </span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {status?.tenant.monthly_usage_count ?? 0} / {status?.tenant.max_tlfs === 999999 ? "Unlimited" : status?.tenant.max_tlfs}
                  </span>
                </div>
                <div className="w-full bg-gray-100 dark:bg-gray-800 h-2 rounded-full overflow-hidden">
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
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-6">
                Tenant billing period ends: {new Date(status.tenant.current_period_end).toLocaleDateString("en-US")} (Quotas reset monthly)
              </p>
            )}
          </div>
        </div>



        {/* 四层级方案定价网格 */}
        <div>
          <div className="text-center max-w-xl mx-auto mb-10">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Choose a Plan to Fit Your Needs</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
              Whether you are an independent programmer or a clinical biostatistics team, we have custom tiers and SLA support for you.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 items-stretch">
            {/* Plan 1: Free */}
            <div className="bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl p-6 shadow-sm flex flex-col justify-between hover:shadow-md transition-shadow">
              <div>
                <h4 className="text-lg font-bold text-gray-900 dark:text-white">Free Plan</h4>
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">Ideal for evaluating the platform and initial trial</p>
                <div className="my-6">
                  <span className="text-3xl font-extrabold text-gray-900 dark:text-white">$0</span>
                  <span className="text-gray-400 dark:text-gray-500 text-sm font-medium"> / Forever</span>
                </div>
                <hr className="border-gray-100 dark:border-gray-800 my-4" />
                <ul className="space-y-3 text-sm text-gray-600 dark:text-gray-400">
                  <li className="flex items-start gap-2.5">
                    <Check className="h-4.5 w-4.5 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <span>Up to 1 Study project</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <Check className="h-4.5 w-4.5 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <span>Up to 10 TLF generation runs / month</span>
                  </li>
                  <li className="flex items-start gap-2.5 text-gray-300 dark:text-gray-700">
                    <Check className="h-4.5 w-4.5 text-gray-300 dark:text-gray-700 flex-shrink-0 mt-0.5" />
                    <span>No collaborative team workspaces</span>
                  </li>
                  <li className="flex items-start gap-2.5 text-gray-300 dark:text-gray-700">
                    <Check className="h-4.5 w-4.5 text-gray-300 dark:text-gray-700 flex-shrink-0 mt-0.5" />
                    <span>No AI-powered SAP error correction</span>
                  </li>
                </ul>
              </div>
              <div className="mt-8">
                <button
                  disabled
                  className="w-full bg-gray-50 dark:bg-gray-900 text-gray-400 dark:text-gray-600 border border-gray-200 dark:border-gray-800 py-2.5 rounded-xl text-sm font-bold cursor-not-allowed"
                >
                  {currentUserPlan === "free" && currentTenantPlan === "free" ? "Default" : "Basic Free"}
                </button>
              </div>
            </div>

            {/* Plan 2: Pro */}
            <div className="bg-white dark:bg-gray-950 border-2 border-indigo-600/30 dark:border-indigo-400/30 rounded-2xl p-6 shadow-md flex flex-col justify-between hover:shadow-lg transition-shadow relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-indigo-600 text-white text-[10px] uppercase font-bold tracking-wider px-3 py-1 rounded-full shadow-sm">
                Recommended
              </div>
              <div>
                <h4 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-1.5">
                  Pro Plan
                  <Zap className="h-4 w-4 text-indigo-500" />
                </h4>
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">Recommended for independent biostatisticians and clinical programmers</p>
                <div className="my-6">
                  <span className="text-3xl font-extrabold text-gray-900 dark:text-white">$29</span>
                  <span className="text-gray-400 dark:text-gray-500 text-sm font-medium"> / Month</span>
                </div>
                <hr className="border-gray-100 dark:border-gray-800 my-4" />
                <ul className="space-y-3 text-sm text-gray-600 dark:text-gray-400">
                  <li className="flex items-start gap-2.5">
                    <Check className="h-4.5 w-4.5 text-indigo-500 flex-shrink-0 mt-0.5" />
                    <span>Up to 50 Study projects</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <Check className="h-4.5 w-4.5 text-indigo-500 flex-shrink-0 mt-0.5" />
                    <span>Up to 500 TLF generation runs / month</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <Check className="h-4.5 w-4.5 text-indigo-500 flex-shrink-0 mt-0.5" />
                    <span>Full access to Figures & SAP parsing</span>
                  </li>
                  <li className="flex items-start gap-2.5 text-gray-300 dark:text-gray-700">
                    <Check className="h-4.5 w-4.5 text-gray-300 dark:text-gray-700 flex-shrink-0 mt-0.5" />
                    <span>Strictly for single-user workspaces</span>
                  </li>
                </ul>
              </div>
              <div className="mt-8">
                {currentUserPlan === "pro" ? (
                  <button
                    disabled
                    className="w-full bg-indigo-50 dark:bg-indigo-950/20 text-indigo-600 dark:text-indigo-400 border border-indigo-100 dark:border-indigo-900/50 py-2.5 rounded-xl text-sm font-bold"
                  >
                    Active (Personal Pro)
                  </button>
                ) : (
                  <button
                    onClick={() => handleUpgrade("pro", variantPro)}
                    disabled={checkoutLoading !== null}
                    className="w-full bg-indigo-600 hover:bg-indigo-700 active:scale-[0.98] text-white py-2.5 rounded-xl text-sm font-bold shadow-sm transition-all flex items-center justify-center gap-1.5"
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
            <div className="bg-white dark:bg-gray-950 border-2 border-violet-600 dark:border-violet-400 rounded-2xl p-6 shadow-md flex flex-col justify-between hover:shadow-lg transition-shadow relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-violet-600 text-white text-[10px] uppercase font-bold tracking-wider px-3 py-1 rounded-full shadow-sm">
                For Teams
              </div>
              <div>
                <h4 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-1.5">
                  Plus Plan
                  <Sparkles className="h-4 w-4 text-violet-500" />
                </h4>
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">Best for clinical trial groups and CRO departments</p>
                <div className="my-6">
                  <span className="text-3xl font-extrabold text-gray-900 dark:text-white">$99</span>
                  <span className="text-gray-400 dark:text-gray-500 text-sm font-medium"> / Month</span>
                </div>
                <hr className="border-gray-100 dark:border-gray-800 my-4" />
                <ul className="space-y-3 text-sm text-gray-600 dark:text-gray-400">
                  <li className="flex items-start gap-2.5">
                    <Check className="h-4.5 w-4.5 text-violet-500 flex-shrink-0 mt-0.5" />
                    <span>Up to 200 Study projects</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <Check className="h-4.5 w-4.5 text-violet-500 flex-shrink-0 mt-0.5" />
                    <span>Up to 5000 shared TLF runs / month</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <Check className="h-4.5 w-4.5 text-violet-500 flex-shrink-0 mt-0.5" />
                    <span>Collaborative workspaces up to 10 members</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <Check className="h-4.5 w-4.5 text-violet-500 flex-shrink-0 mt-0.5" />
                    <span>AI corrections & DOCX format export unlocked</span>
                  </li>
                </ul>
              </div>
              <div className="mt-8">
                {currentTenantPlan === "plus" ? (
                  <button
                    disabled
                    className="w-full bg-violet-50 dark:bg-violet-950/20 text-violet-600 dark:text-violet-400 border border-violet-100 dark:border-violet-900/50 py-2.5 rounded-xl text-sm font-bold"
                  >
                    Active (Tenant Plus)
                  </button>
                ) : (
                  <button
                    onClick={() => handleUpgrade("plus", variantPlus)}
                    disabled={checkoutLoading !== null}
                    className="w-full bg-violet-600 hover:bg-violet-700 active:scale-[0.98] text-white py-2.5 rounded-xl text-sm font-bold shadow-sm transition-all flex items-center justify-center gap-1.5"
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
            <div className="bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl p-6 shadow-sm flex flex-col justify-between hover:shadow-md transition-shadow">
              <div>
                <h4 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-1.5">
                  Enterprise Plan
                  <Shield className="h-4 w-4 text-emerald-500" />
                </h4>
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">Dedicated deployment for large CROs & biotechs</p>
                <div className="my-6">
                  <span className="text-3xl font-extrabold text-gray-900 dark:text-white">Custom</span>
                  <span className="text-gray-400 dark:text-gray-500 text-sm font-medium"> / Annual</span>
                </div>
                <hr className="border-gray-100 dark:border-gray-800 my-4" />
                <ul className="space-y-3 text-sm text-gray-600 dark:text-gray-400">
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
                    className="w-full bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-900/50 py-2.5 rounded-xl text-sm font-bold"
                  >
                    Active (Enterprise)
                  </button>
                ) : (
                  <a
                    href="mailto:info@xwqin.com?subject=Clinical Trial TLF Generator Enterprise Inquiry"
                    className="w-full bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-100 dark:hover:bg-gray-200 dark:text-gray-950 py-2.5 rounded-xl text-sm font-bold shadow-sm transition-all flex items-center justify-center gap-1.5"
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
        <div className="bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-800 rounded-2xl p-6 shadow-sm max-w-4xl mx-auto">
          <h3 className="text-xl font-bold mb-6 text-gray-900 dark:text-white flex items-center gap-2">
            <HelpCircle className="h-5.5 w-5.5 text-indigo-600" />
            Frequently Asked Questions about Billing
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-gray-600 dark:text-gray-400">
            <div>
              <h5 className="font-semibold text-gray-900 dark:text-white">Do Personal Pro and Team Plus conflict?</h5>
              <p className="mt-1 text-xs leading-relaxed">
                No. If a workspace is upgraded to Plus (Team), all collaborators automatically inherit the Plus quotas and features without needing individual Pro plans. If the workspace is on the Free tier, individual Pro subscribers still access advanced features within their workspaces.
              </p>
            </div>
            <div>
              <h5 className="font-semibold text-gray-900 dark:text-white">How do I manage refunds, payment methods, or cancellations?</h5>
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


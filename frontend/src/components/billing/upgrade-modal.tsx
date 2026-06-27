"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertCircle, ArrowRight, X, Sparkles } from "lucide-react";

/**
 * 全局超额拦截弹窗组件 (UpgradeModal)。
 * 监听全局 quota-exceeded 事件，当后端接口返回 402 时，弹出精美的引导升级提示弹窗。
 */
export function UpgradeModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState("您的套餐额度已用尽，请升级以继续使用。");
  const router = useRouter();

  useEffect(() => {
    /**
     * 响应配额超额自定义事件。
     * @param e 自定义事件对象，携带有后端返回的具体拦截原因
     */
    const handleQuotaExceeded = (e: Event) => {
      const customEvent = e as CustomEvent<{ message?: string }>;
      if (customEvent.detail && customEvent.detail.message) {
        setMessage(customEvent.detail.message);
      } else {
        setMessage("您的可用项目或报告生成额度已达到当前套餐上限。");
      }
      setIsOpen(true);
    };

    window.addEventListener("quota-exceeded", handleQuotaExceeded);
    return () => {
      window.removeEventListener("quota-exceeded", handleQuotaExceeded);
    };
  }, []);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm transition-opacity duration-300">
      <div className="relative w-full max-w-md transform rounded-2xl bg-white dark:bg-gray-950 p-6 shadow-2xl transition-all border border-gray-100 dark:border-gray-800 scale-100 animate-in fade-in zoom-in-95 duration-200">
        
        {/* 关闭按钮 */}
        <button
          onClick={() => setIsOpen(false)}
          className="absolute right-4 top-4 rounded-full p-1 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-900 transition-colors"
          title="关闭"
        >
          <X className="h-5 w-5" />
        </button>

        {/* 弹窗内容 */}
        <div className="flex flex-col items-center text-center mt-2">
          {/* 彩色警告图标 */}
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-amber-50 dark:bg-amber-950/50 text-amber-500 mb-4 animate-bounce">
            <AlertCircle className="h-6 w-6" />
          </div>

          <h3 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-1.5 justify-center">
            额度已用尽
            <Sparkles className="h-4.5 w-4.5 text-indigo-500" />
          </h3>
          
          <p className="mt-3 text-sm text-gray-600 dark:text-gray-400 leading-relaxed px-2">
            {message}
          </p>

          <div className="mt-6 w-full space-y-3">
            {/* 立即升级按钮 */}
            <button
              onClick={() => {
                setIsOpen(false);
                router.push("/billing");
              }}
              className="w-full flex items-center justify-center gap-1.5 bg-indigo-600 hover:bg-indigo-700 active:scale-[0.98] text-white py-3 rounded-xl text-sm font-semibold shadow-md transition-all duration-150"
            >
              升级获取更多额度
              <ArrowRight className="h-4 w-4" />
            </button>

            {/* 暂不升级按钮 */}
            <button
              onClick={() => setIsOpen(false)}
              className="w-full bg-gray-50 hover:bg-gray-100 dark:bg-gray-900 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 py-3 rounded-xl text-sm font-semibold transition-all border border-gray-100 dark:border-gray-800"
            >
              暂不升级
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

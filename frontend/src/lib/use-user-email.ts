"use client";

import { useEffect, useState } from "react";
import { useSessionContext } from "supertokens-auth-react/recipe/session";

/**
 * 获取当前登录用户电子邮箱的 React 自定义 Hook。
 * 
 * 优先级机制：
 * 1. 优先读取 SuperTokens Session 访问令牌中的 accessTokenPayload.email（高速本地解析）。
 * 2. 若未登录（doesSessionExist 为 false），立即结束加载并返回 null，绝不盲目请求受保护接口。
 * 3. 仅在已登录但令牌暂未写入 email 时，降级向 /api/v1/users/me 请求用户真实身份。
 *
 * @returns {{ email: string | null; loading: boolean }} 用户邮箱字符串及加载状态
 */
export function useUserEmail(): {
  email: string | null;
  loading: boolean;
} {
  const session = useSessionContext();
  const [email, setEmail] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // 在 effect 外部读取 payload email 与 doesSessionExist 避免 TS 类型收窄问题
  const doesSessionExist = !session.loading ? session.doesSessionExist : false;
  const payloadEmail = !session.loading && session.doesSessionExist ? session.accessTokenPayload?.email : undefined;

  useEffect(() => {
    // 会话处于加载阶段时等待
    if (session.loading) return;

    // 未登录时直接置空并返回，严禁向后端发送 401 探针请求
    if (!doesSessionExist) {
      setEmail(null);
      setLoading(false);
      return;
    }

    // 优先采用 token payload 中的 email
    if (payloadEmail) {
      setEmail(payloadEmail);
      setLoading(false);
      return;
    }

    // 仅已登录且 payload 无 email 时降级查询后端
    fetch("/api/v1/users/me")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data?.email) setEmail(data.email);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [session.loading, doesSessionExist, payloadEmail]);

  return { email, loading };
}


"use client";

import SuperTokens from "supertokens-auth-react";
import EmailPassword from "supertokens-auth-react/recipe/emailpassword";
import Session from "supertokens-auth-react/recipe/session";

// 运行时从浏览器地址推断，避免构建时硬编码
const websiteDomain =
  typeof window !== "undefined"
    ? window.location.origin
    : (process.env.NEXT_PUBLIC_SUPERTOKENS_WEBSITE_DOMAIN ||
       process.env.NEXT_PUBLIC_VERCEL_URL ||
       "http://localhost:3000");

// 运行时从浏览器地址推断 API 地址（auth 请求通过 Next.js rewrite 代理到后端）
// 构建时不需要知道具体域名，解决了 NEXT_PUBLIC_* 在 Docker 构建时被编译的问题
const apiDomain =
  typeof window !== "undefined"
    ? window.location.origin
    : (process.env.NEXT_PUBLIC_SUPERTOKENS_API_DOMAIN ||
       process.env.NEXT_PUBLIC_VERCEL_URL ||
       "http://localhost:3000");

if (typeof window !== "undefined") {
  const recipeList: any[] = [
    EmailPassword.init(),
    Session.init(),
  ];

  const googleId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
  const githubId = process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID;
  const microsoftId = process.env.NEXT_PUBLIC_MICROSOFT_CLIENT_ID;

  if (googleId || githubId || microsoftId) {
    const ThirdParty = require("supertokens-auth-react/recipe/thirdparty").default;
    const providers: any[] = [];

    if (googleId) {
      const Google = require("supertokens-auth-react/recipe/thirdparty").Google;
      providers.push(Google.init({ clientId: googleId }));
    }
    if (githubId) {
      const Github = require("supertokens-auth-react/recipe/thirdparty").Github;
      providers.push(Github.init({ clientId: githubId }));
    }
    if (microsoftId) {
      const ActiveDirectory = require("supertokens-auth-react/recipe/thirdparty").ActiveDirectory;
      providers.push(ActiveDirectory.init({ id: "microsoft", name: "Microsoft" }));
    }

    recipeList.push(
      ThirdParty.init({ signInAndUpFeature: { providers } })
    );
  }

  SuperTokens.init({
    appInfo: {
      appName: "TLF",
      apiDomain,
      websiteDomain,
      apiBasePath: "/api/v1/auth",
      websiteBasePath: "/auth",
    },
    recipeList,
  });

  // 全局劫持 window.fetch 以拦截 402 计费超额响应并派发升级事件
  if (typeof window !== "undefined") {
    const originalFetch = window.fetch;
    window.fetch = async function (...args) {
      const response = await originalFetch(...args);
      if (response.status === 402) {
        try {
          const clone = response.clone();
          const errData = await clone.json();
          const message = errData.detail || "您的项目或生成次数已达到当前订阅额度上限。";
          window.dispatchEvent(
            new CustomEvent("quota-exceeded", { detail: { message } })
          );
        } catch (e) {
          window.dispatchEvent(
            new CustomEvent("quota-exceeded", {
              detail: { message: "您的可用额度已用尽，请升级套餐。" },
            })
          );
        }
      }
      return response;
    };
  }
}


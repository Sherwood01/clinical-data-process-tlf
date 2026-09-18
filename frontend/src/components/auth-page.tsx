"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSessionContext } from "supertokens-auth-react/recipe/session";
import { AuthPage as SuperTokensAuthPage } from "supertokens-auth-react/ui";
import { ThirdPartyPreBuiltUI } from "supertokens-auth-react/recipe/thirdparty/prebuiltui";
import { EmailPasswordPreBuiltUI } from "supertokens-auth-react/recipe/emailpassword/prebuiltui";

export function AuthPage() {
  const session = useSessionContext();
  const router = useRouter();

  useEffect(() => {
    if (!session.loading && session.doesSessionExist) {
      router.push("/dashboard");
    }
  }, [session.loading, session, router]);

  const hasOAuth = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID
    || process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID
    || process.env.NEXT_PUBLIC_MICROSOFT_CLIENT_ID;
  const preBuiltUIList = hasOAuth
    ? [ThirdPartyPreBuiltUI, EmailPasswordPreBuiltUI]
    : [EmailPasswordPreBuiltUI];

  return <SuperTokensAuthPage preBuiltUIList={preBuiltUIList} />;
}

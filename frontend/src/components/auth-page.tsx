"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSessionContext } from "supertokens-auth-react/recipe/session";
import { ThirdPartyEmailPasswordPreBuiltUI } from "supertokens-auth-react/recipe/thirdpartyemailpassword/prebuiltui";

export function AuthPage() {
  const session = useSessionContext();
  const router = useRouter();

  useEffect(() => {
    if (session.loading === false && session.doesSessionExist) {
      router.push("/dashboard");
    }
  }, [session.loading, session.doesSessionExist, router]);

  return <ThirdPartyEmailPasswordPreBuiltUI />;
}

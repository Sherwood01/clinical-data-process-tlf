"use client";

import SuperTokens from "supertokens-auth-react";
import ThirdPartyEmailPassword from "supertokens-auth-react/recipe/thirdpartyemailpassword";
import Session from "supertokens-auth-react/recipe/session";

const websiteDomain =
  process.env.NEXT_PUBLIC_SUPERTOKENS_WEBSITE_DOMAIN ||
  process.env.NEXT_PUBLIC_VERCEL_URL ||
  "http://localhost:3000";

const apiDomain =
  process.env.NEXT_PUBLIC_SUPERTOKENS_API_DOMAIN ||
  process.env.NEXT_PUBLIC_VERCEL_URL ||
  "http://localhost:3000";

SuperTokens.init({
  appInfo: {
    appName: "TLF",
    apiDomain,
    websiteDomain,
    apiBasePath: "/api/v1/auth",
    websiteBasePath: "/auth",
  },
  recipeList: [
    ThirdPartyEmailPassword.init(),
    Session.init(),
  ],
});

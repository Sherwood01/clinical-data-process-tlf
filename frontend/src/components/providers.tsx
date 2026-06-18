"use client";

import { SuperTokensWrapper } from "supertokens-auth-react";
import { ThemeProvider } from "@/components/theme-provider";

import "@/lib/supertokens";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SuperTokensWrapper>
      <ThemeProvider
        defaultTheme="system"
        enableSystem
        disableTransitionOnChange
      >
        {children}
      </ThemeProvider>
    </SuperTokensWrapper>
  );
}

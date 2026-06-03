"use client";

import { StackProvider, StackClientApp } from "@hexclave/next";
import { ThemeProvider } from "@/components/theme-provider";

const stackApp = new StackClientApp({
  tokenStore: "cookie",
  urls: {
    home: "/dashboard",
    signIn: "/handler/sign-in",
    signUp: "/handler/sign-up",
  },
});

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <StackProvider app={stackApp}>
      <ThemeProvider
        attribute="class"
        defaultTheme="system"
        enableSystem
        disableTransitionOnChange
      >
        {children}
      </ThemeProvider>
    </StackProvider>
  );
}

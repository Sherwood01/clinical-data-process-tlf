"use client";

import { StackProvider, StackClientApp } from "@hexclave/next";
import { ThemeProvider } from "@/components/theme-provider";
import { TooltipProvider } from "@hexclave/ui";

const stackApp = new StackClientApp({
  baseUrl: {
    browser: process.env.NEXT_PUBLIC_STACK_URL || "http://localhost:3100",
    server: process.env.NEXT_PUBLIC_STACK_API_URL_SERVER || "http://localhost:3000",
  },
  projectId: process.env.NEXT_PUBLIC_STACK_PROJECT_ID || "internal",
  publishableClientKey: process.env.NEXT_PUBLIC_STACK_PUBLISHABLE_CLIENT_KEY || "12345678",
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
        defaultTheme="system"
        enableSystem
        disableTransitionOnChange
      >
        <TooltipProvider>
          {children}
        </TooltipProvider>
      </ThemeProvider>
    </StackProvider>
  );
}

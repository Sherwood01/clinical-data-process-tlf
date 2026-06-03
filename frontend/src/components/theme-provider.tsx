"use client";

export function ThemeProvider({
  children,
}: {
  children: React.ReactNode;
  [key: string]: any;
}) {
  return <>{children}</>;
}

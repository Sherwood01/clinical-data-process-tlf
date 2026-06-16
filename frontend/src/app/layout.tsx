import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/components/providers";

// Prevent FOUC by applying dark class before React hydrates
const antiFoucScript = `
try {
  var t = localStorage.getItem("theme");
  if (t === "dark" || (!t && matchMedia("(prefers-color-scheme: dark)").matches)) {
    document.documentElement.classList.add("dark");
  }
} catch(e){}
`;

export const metadata: Metadata = {
  title: "TLF Report Generator",
  description: "AI-powered clinical trial TLF report generation platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: antiFoucScript }} />
      </head>
      <body className="min-h-full">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

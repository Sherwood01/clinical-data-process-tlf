"use client";

import Link from "next/link";
import { useUser } from "@hexclave/next";

export function LandingPage() {
  const user = useUser();

  if (user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <h1 className="text-3xl font-bold mb-4">Welcome back!</h1>
          <p className="text-gray-600 mb-6">
            Signed in as {user.displayName || user.primaryEmail}
          </p>
          <Link
            href="/dashboard"
            className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
          >
            Go to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen">
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold">TLF Report Generator</h1>
          <div className="flex gap-4">
            <Link
              href="/handler/sign-in"
              className="px-4 py-2 text-sm font-medium hover:text-blue-600"
            >
              Sign In
            </Link>
            <Link
              href="/handler/sign-up"
              className="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1 container mx-auto px-4 py-16">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-4xl font-bold mb-6">
            Generate Clinical Trial TLF Reports with AI
          </h2>
          <p className="text-lg text-gray-600 mb-8">
            Upload your SAP documents and ADaM datasets, and let our AI-powered
            platform generate professional TLF (Tables, Listings, Figures)
            reports for your clinical studies.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            <div className="p-6 border rounded-lg">
              <h3 className="font-semibold mb-2">1. Upload</h3>
              <p className="text-sm text-gray-600">
                Upload your SAP document and ADaM datasets
              </p>
            </div>
            <div className="p-6 border rounded-lg">
              <h3 className="font-semibold mb-2">2. Configure</h3>
              <p className="text-sm text-gray-600">
                Review auto-detected TOC entries and select reports
              </p>
            </div>
            <div className="p-6 border rounded-lg">
              <h3 className="font-semibold mb-2">3. Generate</h3>
              <p className="text-sm text-gray-600">
                Get professional PDF reports in minutes
              </p>
            </div>
          </div>

          <Link
            href="/handler/sign-up"
            className="inline-block bg-blue-600 text-white px-8 py-4 rounded-lg text-lg font-medium hover:bg-blue-700"
          >
            Start Free Trial
          </Link>
        </div>
      </main>

      <footer className="border-t py-8 text-center text-sm text-gray-500">
        TLF Report Generator Platform
      </footer>
    </div>
  );
}

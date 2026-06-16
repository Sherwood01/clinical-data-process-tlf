"use client";

import Link from "next/link";
import { useUser } from "@hexclave/next";
import {
  Upload,
  FileSearch,
  Sparkles,
  Shield,
  BarChart3,
  Download,
  ArrowRight,
  CheckCircle,
  Quote,
} from "lucide-react";

function Github({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>
    </svg>
  );
}

const features = [
  {
    icon: Upload,
    title: "Upload Datasets",
    description:
      "Upload ADaM datasets in SAS, XPT, or CSV format. Our platform automatically validates your data structure.",
  },
  {
    icon: FileSearch,
    title: "Parse SAP Documents",
    description:
      "AI-powered parsing of Statistical Analysis Plans. Automatically extracts TOC entries and report specifications.",
  },
  {
    icon: Sparkles,
    title: "AI Report Generation",
    description:
      "Advanced AI selects the right macro templates and generates production-ready SAS code for your TLFs.",
  },
  {
    icon: Shield,
    title: "Validation Ready",
    description:
      "All outputs include comprehensive audit trails, making regulatory validation straightforward.",
  },
  {
    icon: BarChart3,
    title: "Real-time Progress",
    description:
      "Monitor report generation progress in real-time. Get instant notifications on completion or issues.",
  },
  {
    icon: Download,
    title: "PDF Export",
    description:
      "Generate professional, publication-ready PDF reports with consistent formatting and branding.",
  },
];

const steps = [
  {
    number: "01",
    title: "Upload SAP & ADaM",
    description:
      "Upload your Statistical Analysis Plan (PDF/DOCX) and ADaM datasets. Our system automatically validates formats.",
  },
  {
    number: "02",
    title: "Review & Configure",
    description:
      "Review AI-extracted TOC entries, select desired outputs, and configure report parameters.",
  },
  {
    number: "03",
    title: "Generate Reports",
    description:
      "Generate professional TLF reports with one click. Download formatted PDFs ready for submission.",
  },
];

const testimonials = [
  {
    quote:
      "This platform cut our TLF generation time from days to hours. The AI-powered TOC extraction is remarkably accurate.",
    author: "Dr. Sarah Chen",
    role: "Senior Biostatistician",
  },
  {
    quote:
      "The validation-ready outputs have streamlined our regulatory submission process significantly.",
    author: "Michael Roberts",
    role: "Clinical Data Manager",
  },
];

export function LandingPage() {
  const user = useUser();

  if (user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-background to-muted/50">
        <div className="text-center max-w-md mx-auto px-4">
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary shadow-lg">
            <CheckCircle className="h-8 w-8 text-primary-foreground" />
          </div>
          <h1 className="text-3xl font-bold mb-2">Welcome back!</h1>
          <p className="text-muted-foreground mb-8">
            Signed in as{" "}
            <span className="font-medium text-foreground">
              {user.displayName || user.primaryEmail}
            </span>
          </p>
          <Link
            href="/dashboard"
            className="inline-flex items-center justify-center h-10 rounded-md px-8 text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Go to Dashboard
            <ArrowRight className="ml-2 h-4 w-4" />
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen">
      {/* Navigation */}
      <header className="sticky top-0 z-50 border-b bg-background/80 backdrop-blur-sm">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground text-sm font-bold">
              T
            </div>
            <span className="font-semibold">TLF Report</span>
          </div>
          <div className="flex items-center gap-4">
            <a
              href="https://github.com/Sherwood01/clinical-data-process"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center h-9 w-9 rounded-md hover:bg-accent hover:text-accent-foreground transition-colors text-muted-foreground"
              title="GitHub 仓库"
            >
              <Github className="h-5 w-5" />
            </a>
            <Link
              href="/handler/sign-in"
              className="inline-flex items-center justify-center h-9 rounded-md px-4 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/handler/sign-up"
              className="inline-flex items-center justify-center h-9 rounded-md px-4 py-2 text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden border-b">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-primary/10 to-purple-500/5" />
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.03)_1px,transparent_1px)] bg-[size:64px_64px]" />

        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-20 md:py-32">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mb-6 inline-flex items-center rounded-full border bg-muted/50 px-4 py-1.5 text-sm text-muted-foreground">
              <Sparkles className="mr-2 h-3.5 w-3.5 text-primary" />
              AI-Powered Clinical Trial Reporting
            </div>
            <h1 className="text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
              Generate Clinical Trial
              <span className="block text-primary">TLF Reports with AI</span>
            </h1>
            <p className="mt-6 text-lg text-muted-foreground max-w-2xl mx-auto">
              Upload your SAP documents and ADaM datasets. Let our AI-powered
              platform automatically generate professional TLF reports for your
              clinical studies in minutes.
            </p>
            <div className="mt-10 flex items-center justify-center gap-4">
              <Link
                href="/handler/sign-up"
                className="inline-flex items-center justify-center h-10 rounded-md px-8 text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                Start Free Trial
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
              <a
                href="https://github.com/Sherwood01/clinical-data-process"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center h-10 rounded-md px-8 text-sm font-medium border border-input bg-background hover:bg-accent hover:text-accent-foreground transition-colors"
              >
                <Github className="mr-2 h-4 w-4" />
                GitHub
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 md:py-28">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight">
              Everything you need for TLF generation
            </h2>
            <p className="mt-4 text-muted-foreground">
              From data upload to final PDF — all in one platform.
            </p>
          </div>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <div
                  key={feature.title}
                  className="group rounded-xl border bg-card p-6 transition-all hover:shadow-md hover:border-primary/20"
                >
                  <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="font-semibold mb-2">{feature.title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="border-t bg-muted/30 py-20 md:py-28">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight">
              How it works
            </h2>
            <p className="mt-4 text-muted-foreground">
              Three simple steps to generate professional TLF reports.
            </p>
          </div>
          <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
            {steps.map((step, i) => (
              <div key={i} className="relative text-center">
                {i < steps.length - 1 && (
                  <div className="hidden md:block absolute top-8 left-[60%] w-[80%] h-px border-t border-dashed border-border" />
                )}
                <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary text-primary-foreground text-xl font-bold">
                  {step.number}
                </div>
                <h3 className="text-lg font-semibold mb-2">{step.title}</h3>
                <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-20 md:py-28">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight">
              Trusted by clinical researchers
            </h2>
          </div>
          <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
            {testimonials.map((t) => (
              <div
                key={t.author}
                className="rounded-xl border bg-card p-8"
              >
                <Quote className="h-8 w-8 text-primary/40 mb-4" />
                <p className="text-muted-foreground mb-6 leading-relaxed">
                  &ldquo;{t.quote}&rdquo;
                </p>
                <div>
                  <p className="font-semibold text-sm">{t.author}</p>
                  <p className="text-sm text-muted-foreground">{t.role}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t bg-gradient-to-br from-primary/5 via-primary/10 to-purple-500/5">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-20 text-center">
          <h2 className="text-3xl font-bold tracking-tight mb-4">
            Ready to get started?
          </h2>
          <p className="text-muted-foreground mb-8 max-w-md mx-auto">
            Start generating professional TLF reports for your clinical studies
            today.
          </p>
          <Link
            href="/handler/sign-up"
            className="inline-flex items-center justify-center h-10 rounded-md px-8 text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Start Free Trial
            <ArrowRight className="ml-2 h-4 w-4" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary text-primary-foreground text-xs font-bold">
                  T
                </div>
                <span className="text-sm font-medium">TLF Report Generator</span>
              </div>
              <a
                href="https://github.com/Sherwood01/clinical-data-process"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-foreground transition-colors"
                title="GitHub"
              >
                <Github className="h-5 w-5" />
              </a>
            </div>
            <p className="text-sm text-muted-foreground">
              &copy; {new Date().getFullYear()} TLF Report Generator. All
              rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

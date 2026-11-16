"use client";

import { useSessionContext } from "supertokens-auth-react/recipe/session";
import Link from "next/link";
import { useUserEmail } from "@/lib/use-user-email";
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
  const session = useSessionContext();
  const { email } = useUserEmail();
  const isLoggedIn = !session.loading && session.doesSessionExist;

  if (isLoggedIn) {
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
              {email || (!session.loading ? session.userId : "") || ""}
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
    <div className="flex flex-col min-h-screen scroll-smooth">
      {/* Navigation */}
      <header className="sticky top-0 z-50 border-b border-slate-200 dark:border-slate-800 bg-white/85 dark:bg-[#0a0f1d]/85 backdrop-blur-md transition-colors">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#1e3a8a] dark:bg-[#1e40af] text-white text-sm font-bold shadow-xs">
              T
            </div>
            <span className="font-bold text-slate-900 dark:text-slate-100 tracking-tight">TLF Report</span>
          </div>
          <nav className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors">
              Features
            </a>
            <a href="#how-it-works" className="text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors">
              Solutions
            </a>
            <a href="#testimonials" className="text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors">
              Reviews
            </a>
            <a href="#pricing" className="text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors">
              Pricing
            </a>
            <a href="#contact" className="text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors">
              Contact Us
            </a>
          </nav>
          <div className="flex items-center gap-4">
            <a
              href="https://github.com/Sherwood01/clinical-data-process-tlf"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center h-9 w-9 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
              title="GitHub 仓库"
            >
              <Github className="h-5 w-5" />
            </a>
            <Link
              href="/auth/sign-in"
              className="inline-flex items-center justify-center h-9 rounded-md px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/auth/sign-up"
              className="inline-flex items-center justify-center h-9 rounded-md px-4 py-2 text-sm font-semibold bg-[#1e3a8a] hover:bg-[#172554] dark:bg-[#1e40af] dark:hover:bg-[#1d4ed8] text-white shadow-xs transition-colors active:scale-95"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-[#070b14]/70">
        {/* Subtle grid pattern background */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(100,116,139,.07)_1px,transparent_1px),linear-gradient(90deg,rgba(100,116,139,.07)_1px,transparent_1px)] bg-[size:48px_48px] dark:bg-[linear-gradient(rgba(148,163,184,.04)_1px,transparent_1px),linear-gradient(90deg,rgba(148,163,184,.04)_1px,transparent_1px)]" />

        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-20 md:py-32">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mb-6 inline-flex items-center gap-2 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/80 px-3.5 py-1 text-xs sm:text-sm font-semibold text-[#1e3a8a] dark:text-[#93c5fd] shadow-2xs">
              <Sparkles className="h-3.5 w-3.5" />
              <span>AI-Powered Clinical Trial Reporting &amp; ADaM Validation</span>
            </div>
            <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white sm:text-5xl md:text-6xl leading-tight">
              Generate Clinical Trial <br className="hidden sm:inline" />
              <span className="text-[#1e3a8a] dark:text-[#60a5fa]">TLF Reports with AI</span>
            </h1>
            <p className="mt-6 text-base sm:text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto leading-relaxed">
              Upload your SAP documents and ADaM datasets. Let our AI-powered
              platform automatically generate professional, 21 CFR Part 11 compliant TLF reports for your
              clinical studies in minutes.
            </p>
            <div className="mt-10 flex items-center justify-center gap-4">
              <Link
                href="/auth/sign-up"
                className="inline-flex items-center justify-center h-10 rounded-md px-8 text-sm font-semibold bg-[#1e3a8a] hover:bg-[#172554] dark:bg-[#1e40af] dark:hover:bg-[#1d4ed8] text-white shadow-xs transition-colors active:scale-95"
              >
                Start Free Trial
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
              <a
                href="https://github.com/Sherwood01/clinical-data-process-tlf"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center h-10 rounded-md px-8 text-sm font-medium border border-slate-300 dark:border-slate-700 bg-white dark:bg-[#101828] text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 shadow-2xs transition-colors"
              >
                <Github className="mr-2 h-4 w-4" />
                GitHub
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 md:py-28 scroll-mt-16">
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
      <section id="how-it-works" className="border-t bg-muted/30 py-20 md:py-28 scroll-mt-16">
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
      <section id="testimonials" className="py-20 md:py-28 scroll-mt-16">
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

      {/* 定价订阅方案模块 */}
      <section id="pricing" className="py-20 md:py-28 border-t bg-muted/10 scroll-mt-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight">Subscription Plans & Pricing</h2>
            <p className="mt-4 text-muted-foreground">
              Flexible and efficient subscription tiers tailored for clinical programming and biostatistics teams of all sizes.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 items-stretch">
            {/* Free */}
            <div className="rounded-xl border bg-card p-6 flex flex-col justify-between hover:shadow-md transition-shadow">
              <div>
                <h3 className="text-lg font-bold">Free Plan</h3>
                <p className="text-xs text-muted-foreground mt-1">Ideal for evaluating the platform and initial trial</p>
                <div className="my-6">
                  <span className="text-3xl font-extrabold">$0</span>
                  <span className="text-muted-foreground text-sm"> / Forever</span>
                </div>
                <hr className="my-4 border-muted" />
                <ul className="space-y-3 text-sm text-muted-foreground">
                  <li className="flex items-start gap-2">
                    <CheckCircle className="h-4.5 w-4.5 text-primary flex-shrink-0 mt-0.5" />
                    <span>Up to 1 Study project</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="h-4.5 w-4.5 text-primary flex-shrink-0 mt-0.5" />
                    <span>Up to 10 TLF generation runs / month</span>
                  </li>
                  <li className="flex items-start gap-2 opacity-50">
                    <span>No collaborative team workspaces</span>
                  </li>
                  <li className="flex items-start gap-2 opacity-50">
                    <span>No AI-powered SAP error correction</span>
                  </li>
                </ul>
              </div>
              <div className="mt-8">
                <Link
                  href="/auth/sign-up"
                  className="block w-full text-center h-10 leading-10 rounded-md text-sm font-medium border border-input bg-background hover:bg-accent hover:text-accent-foreground transition-colors"
                >
                  Start for Free
                </Link>
              </div>
            </div>

            {/* Pro */}
            <div className="rounded-xl border-2 border-primary/50 bg-card p-6 flex flex-col justify-between hover:shadow-md transition-shadow relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground text-[10px] uppercase font-bold tracking-wider px-3 py-1 rounded-full shadow-sm">
                For Individuals
              </div>
              <div>
                <h3 className="text-lg font-bold flex items-center gap-1.5 justify-between">
                  <span>Pro Plan</span>
                  <Sparkles className="h-4 w-4 text-primary animate-pulse" />
                </h3>
                <p className="text-xs text-muted-foreground mt-1">Recommended for independent biostatisticians and programmers</p>
                <div className="my-6">
                  <span className="text-3xl font-extrabold">$29</span>
                  <span className="text-muted-foreground text-sm"> / Month</span>
                </div>
                <hr className="my-4 border-muted" />
                <ul className="space-y-3 text-sm text-muted-foreground">
                  <li className="flex items-start gap-2">
                    <CheckCircle className="h-4.5 w-4.5 text-primary flex-shrink-0 mt-0.5" />
                    <span>Up to 50 Study projects</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="h-4.5 w-4.5 text-primary flex-shrink-0 mt-0.5" />
                    <span>Up to 500 TLF generation runs / month</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="h-4.5 w-4.5 text-primary flex-shrink-0 mt-0.5" />
                    <span>Full access to Figures & SAP parsing</span>
                  </li>
                  <li className="flex items-start gap-2 opacity-50">
                    <span>Strictly for single-user workspaces</span>
                  </li>
                </ul>
              </div>
              <div className="mt-8">
                <Link
                  href="/auth/sign-up"
                  className="block w-full text-center h-10 leading-10 rounded-md text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-sm"
                >
                  Subscribe to Pro
                </Link>
              </div>
            </div>

            {/* Plus */}
            <div className="rounded-xl border-2 border-purple-500/50 bg-card p-6 flex flex-col justify-between hover:shadow-md transition-shadow relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-purple-500 text-white text-[10px] uppercase font-bold tracking-wider px-3 py-1 rounded-full shadow-sm">
                For Teams
              </div>
              <div>
                <h3 className="text-lg font-bold">Plus Plan</h3>
                <p className="text-xs text-muted-foreground mt-1">Best for clinical trial groups and CRO departments</p>
                <div className="my-6">
                  <span className="text-3xl font-extrabold">$99</span>
                  <span className="text-muted-foreground text-sm"> / Month</span>
                </div>
                <hr className="my-4 border-muted" />
                <ul className="space-y-3 text-sm text-muted-foreground">
                  <li className="flex items-start gap-2">
                    <CheckCircle className="h-4.5 w-4.5 text-purple-500 flex-shrink-0 mt-0.5" />
                    <span>Up to 200 Study projects</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="h-4.5 w-4.5 text-purple-500 flex-shrink-0 mt-0.5" />
                    <span>Up to 5000 shared TLF runs / month</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="h-4.5 w-4.5 text-purple-500 flex-shrink-0 mt-0.5" />
                    <span>Collaborative workspaces up to 10 members</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="h-4.5 w-4.5 text-purple-500 flex-shrink-0 mt-0.5" />
                    <span>AI corrections & DOCX format export unlocked</span>
                  </li>
                </ul>
              </div>
              <div className="mt-8">
                <Link
                  href="/auth/sign-up"
                  className="block w-full text-center h-10 leading-10 rounded-md text-sm font-medium bg-purple-600 hover:bg-purple-700 text-white transition-colors shadow-sm"
                >
                  Subscribe to Plus
                </Link>
              </div>
            </div>

            {/* Enterprise */}
            <div className="rounded-xl border bg-card p-6 flex flex-col justify-between hover:shadow-md transition-shadow">
              <div>
                <h3 className="text-lg font-bold">Enterprise Plan</h3>
                <p className="text-xs text-muted-foreground mt-1">Dedicated deployment for large CROs & biotechs</p>
                <div className="my-6">
                  <span className="text-3xl font-extrabold">Custom</span>
                  <span className="text-muted-foreground text-sm"> / Annual</span>
                </div>
                <hr className="my-4 border-muted" />
                <ul className="space-y-3 text-sm text-muted-foreground">
                  <li className="flex items-start gap-2">
                    <CheckCircle className="h-4.5 w-4.5 text-primary flex-shrink-0 mt-0.5" />
                    <span>Unlimited Studies & collaborators</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="h-4.5 w-4.5 text-primary flex-shrink-0 mt-0.5" />
                    <span>Dedicated physical / logical isolation</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="h-4.5 w-4.5 text-primary flex-shrink-0 mt-0.5" />
                    <span>Enterprise SLA & custom Figures support</span>
                  </li>
                </ul>
              </div>
              <div className="mt-8">
                <a
                  href="mailto:info@xwqin.com?subject=Clinical Trial TLF Generator Enterprise Inquiry"
                  className="block w-full text-center h-10 leading-10 rounded-md text-sm font-medium border border-input bg-background hover:bg-accent hover:text-accent-foreground transition-colors"
                >
                  Contact Sales
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t bg-gradient-to-br from-primary/5 via-primary/10 to-purple-500/5">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-20 text-center">
          <h2 className="text-3xl font-bold tracking-tight mb-4">
            Ready to generate clinical trial reports faster?
          </h2>
          <p className="text-muted-foreground mb-8 max-w-md mx-auto">
            Sign up now and start generating publication-quality clinical trial outputs in minutes.
          </p>
          <Link
            href="/auth/sign-up"
            className="inline-flex items-center justify-center h-10 rounded-md px-8 text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Start Free Trial
            <ArrowRight className="ml-2 h-4 w-4" />
          </Link>
        </div>
      </section>


      {/* Footer */}
      <footer id="contact" className="border-t py-12">
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
                href="https://github.com/Sherwood01/clinical-data-process-tlf"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-foreground transition-colors"
                title="GitHub"
              >
                <Github className="h-5 w-5" />
              </a>
            </div>
            <div className="flex flex-col md:flex-row items-center gap-6">
              <div className="flex gap-6 text-sm text-muted-foreground">
                <Link href="/terms" className="hover:text-foreground transition-colors">
                  Terms of Service
                </Link>
                <Link href="/privacy" className="hover:text-foreground transition-colors">
                  Privacy Policy
                </Link>
                <a href="mailto:info@xwqin.com?subject=TLF Report Generator Inquiry" className="hover:text-foreground transition-colors">
                  Support: info@xwqin.com
                </a>
              </div>
              <p className="text-sm text-muted-foreground">
                &copy; {new Date().getFullYear()} TLF Report Generator. All
                rights reserved.
              </p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

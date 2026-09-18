"use client";

import { useState } from "react";
import { 
  FileText, Database, HelpCircle, Mail, BookOpen, Layers, CheckCircle2, 
  ChevronDown, ChevronUp, Sparkles, Terminal, Settings, ArrowRight, Eye, Code, Zap
} from "lucide-react";

interface FAQItem {
  q: string;
  a: string;
}

export default function HelpPage() {
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  const faqs: FAQItem[] = [
    {
      q: "How does the system extract the TOC from a Statistical Analysis Plan (SAP)?",
      a: "When you upload your SAP protocol in Word format (.docx), our intelligent parsing algorithm scans the document outline, searching for sections or appendix indexes starting with Section 14 (Table/Figure) or Appendix 16 (Listing). It then breaks down the report numbers, titles, and population categories to dynamically generate and activate your TOC structure."
    },
    {
      q: "What are the naming and file format requirements for ADaM datasets?",
      a: "The analytical pipeline currently processes SAS proprietary dataset formats (.sas7bdat). To allow successful dependency matching, all ADaM filenames must be in lowercase (e.g. adsl.sas7bdat, adae.sas7bdat, adtte.sas7bdat). The generator will automatically inspect the columns based on report type. For example, demographic disposition tables require 'adsl.sas7bdat', while adverse event tables require 'adae.sas7bdat' in addition to 'adsl.sas7bdat'."
    },
    {
      q: "How do I troubleshoot N=0 counts in the table headers?",
      a: "Our system implements adaptive treatment group scanning. During table report generations, the analyzer automatically extracts the planned treatment variable (TRT01PN or TRT01P) from your ADSL dataset and computes treatment-specific N values dynamically. If your table headers show N=0, please double-check that your ADSL dataset contains one of these treatment variables and that the records are populated."
    },
    {
      q: "Can I download and audit the generated TLF report files along with the source code?",
      a: "Yes. The platform provides comprehensive audit trails for regulatory compliance. You can click on any completed job in the history tab to download a ZIP archive containing the generated PDF report, the reproducible Python script (code.py), and the environment execution logs (run.log). You can also click 'Download Study ZIP' on the Study overview to export all successfully generated reports cataloged by Tables, Figures, and Listings."
    },
    {
      q: "How can I upgrade my subscription plan for more generation limits?",
      a: "Free plan accounts have a limitation of 10 generation runs per month. You can visit the 'Billing' menu in the sidebar to view subscription tiers (Pro at 500 runs/month, or Plus/Enterprise for higher thresholds). Subscriptions are securely processed through our checkout checkout system, and limits are updated instantly upon successful transaction."
    }
  ];

  const toggleFaq = (index: number) => {
    setOpenFaq(openFaq === index ? null : index);
  };

  const steps = [
    {
      title: "1. Create Study Workspace",
      desc: "Create a study from the dashboard to initialize isolated data spaces and PostgreSQL Row-Level Security."
    },
    {
      title: "2. Ingest ADaM Datasets",
      desc: "Upload SAS (.sas7bdat) files (e.g., adsl, adae) in the Datasets tab. The system extracts columns and validates variables."
    },
    {
      title: "3. Parse SAP & Extract TOC",
      desc: "Upload your SAP Word document (.docx). The AI engine automatically parses outlines and populates the Table of Contents."
    },
    {
      title: "4. Run AI Agent & Spec Tuner",
      desc: "Interact with the AI Chat assistant to trigger reports, use the Spec Tuner to calibrate VariableSpecs, and generate PDF outputs."
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50/50 py-10 text-gray-900">
      <div className="max-w-5xl mx-auto px-6">
        
        {/* Top Header Card */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-3xl shadow-xl p-8 text-white mb-10 relative overflow-hidden">
          <div className="absolute right-0 bottom-0 translate-x-10 translate-y-10 opacity-10">
            <BookOpen className="h-64 w-64" />
          </div>
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-8">
            <div>
              <span className="bg-white/20 text-blue-100 text-xs px-3.5 py-1 rounded-full font-bold uppercase tracking-wider">
                Official User Manual
              </span>
              <h1 className="text-3xl font-extrabold mt-3">Platform Manual & Documentation</h1>
              <p className="text-blue-100/90 mt-2 max-w-xl text-sm leading-relaxed">
                Welcome to the Clinical TLF Report Generator help center. Find installation workflows, ADaM data formatting requirements, troubleshooting steps, and audit guides.
              </p>
            </div>
            
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-5 border border-white/10 flex flex-col items-center text-center shrink-0">
              <Mail className="h-8 w-8 text-blue-200 mb-2" />
              <span className="text-xs text-blue-200 font-semibold">Technical Support Email</span>
              <a 
                href="mailto:info@xwqin.com" 
                className="text-lg font-bold hover:underline mt-1 text-white"
              >
                info@xwqin.com
              </a>
              <span className="text-[10px] text-blue-200/70 mt-1">24-hour turnaround on weekdays</span>
            </div>
          </div>
        </div>

        {/* User Manual Core Navigation Panels */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Main Document Body */}
          <div className="lg:col-span-2 space-y-10">
            
            {/* Section 1: The Dual-Delivery Architecture */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2 border-b pb-3 mb-4">
                <Zap className="h-5 w-5 text-blue-600" />
                1. Dual-Delivery Architecture
              </h2>
              <div className="space-y-4 text-xs text-gray-600 leading-relaxed">
                <p>
                  To maximize efficiency while meeting regulatory compliance, the platform implements a <strong>Dual-Delivery Architecture</strong>:
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
                  <div className="bg-gray-50 border rounded-xl p-4">
                    <h4 className="font-bold text-gray-800 flex items-center gap-1.5 text-xs mb-2">
                      <Eye className="h-4 w-4 text-emerald-600" />
                      A. Python PDF Preview Line
                    </h4>
                    <p className="text-[11px] text-gray-500">
                      Utilizes our high-speed, local Python analytical engine (pandas, numpy, reportlab) to generate instant tables, figures, and listings. Perfect for rapid web-based verification and report previews.
                    </p>
                  </div>
                  <div className="bg-gray-50 border rounded-xl p-4">
                    <h4 className="font-bold text-gray-800 flex items-center gap-1.5 text-xs mb-2">
                      <Code className="h-4 w-4 text-blue-600" />
                      B. AI Agent SAS Code Line
                    </h4>
                    <p className="text-[11px] text-gray-500">
                      When exporting deliverables for FDA or other health authority compliance audits, our AI Agent auto-generates complete, compilable <strong>SAS programs (.sas files)</strong> utilizing standardized clinical macros.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Section 2: AI Agent & Conversational Assistant */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2 border-b pb-3 mb-4">
                <Sparkles className="h-5 w-5 text-blue-600" />
                2. Interactive AI Chat & Sandbox Executor
              </h2>
              <div className="space-y-3 text-xs text-gray-600 leading-relaxed">
                <p>
                  The system features an <strong>AI Chat Assistant</strong> (accessible via the sidebar chat icon in any study). It serves as your co-pilot:
                </p>
                <ul className="list-disc pl-5 space-y-2 text-[11px]">
                  <li>
                    <strong>Pipeline Orchestrator</strong>: Type natural commands like <code className="bg-gray-100 px-1 py-0.5 rounded font-mono text-[10px]">"Generate Table 14.1.2.1"</code> or <code className="bg-gray-100 px-1 py-0.5 rounded font-mono text-[10px]">"List all uploaded datasets"</code>. The AI Agent uses its ReAct loop to call internal tools and run pipelines.
                  </li>
                  <li>
                    <strong>Sandboxed Python Figure Programmer</strong>: If you ask for a custom chart not supported out-of-the-box (e.g., <code className="bg-gray-100 px-1 py-0.5 rounded font-mono text-[10px]">"Plot a laboratory distribution curve for Hemoglobin"</code>), the AI Agent will dynamically write a custom Python script, run it in a secure docker sandbox, and deliver the output PDF to the chat feed.
                  </li>
                </ul>
              </div>
            </div>

            {/* Section 3: Knowledge Base & Spec Tuner */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2 border-b pb-3 mb-4">
                <Database className="h-5 w-5 text-blue-600" />
                3. Global Knowledge Base & Spec Tuner
              </h2>
              <div className="space-y-3 text-xs text-gray-600 leading-relaxed">
                <p>
                  The <strong>Knowledge Base</strong> acts as the central brain registry of standard algorithms, bridging the user and the AI programmer:
                </p>
                <div className="space-y-3 mt-3">
                  <div className="flex gap-2.5 items-start">
                    <span className="h-2 w-2 rounded-full bg-blue-600 mt-1.5 shrink-0" />
                    <div>
                      <h4 className="font-bold text-gray-800 text-xs">SAS Macro Assets & Auto-Learning</h4>
                      <p className="text-[11px] text-gray-500">
                        Displays the 97 standard SAS macros currently indexed. To add custom clinical logic, upload a <code className="bg-gray-100 px-1 py-0.5 rounded font-mono">.sas</code> file. The backend automatically invokes DeepSeek Flash to extract parameters and index it for AI generation.
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-2.5 items-start">
                    <span className="h-2 w-2 rounded-full bg-blue-600 mt-1.5 shrink-0" />
                    <div>
                      <h4 className="font-bold text-gray-800 text-xs">VariableSpec Tuner (Spec Tuner)</h4>
                      <p className="text-[11px] text-gray-500">
                        When AI encounters a novel table structure, it infers the columns, filters, and variables. Review its draft parameters in the <strong>Spec Tuner</strong>, modify values (e.g. tightening a population filter), and save. Subsequent AI generations will prioritize your manual adjustments.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Step-by-Step Flow */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2 border-b pb-3 mb-4">
                <Layers className="h-5 w-5 text-blue-600" />
                4. End-to-End Operational Workflow
              </h2>
              <div className="space-y-5">
                {steps.map((step, idx) => (
                  <div key={idx} className="flex gap-4 items-start">
                    <div className="flex items-center justify-center bg-blue-50 text-blue-600 rounded-xl p-2.5 shrink-0 font-bold text-sm h-10 w-10 border border-blue-100">
                      0{idx + 1}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 text-sm">{step.title}</h3>
                      <p className="text-gray-500 text-xs leading-relaxed mt-1">{step.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* ADaM Table Specs */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2 border-b pb-3 mb-4">
                <Database className="h-5 w-5 text-blue-600" />
                5. ADaM Dataset Requirements
              </h2>
              <div className="text-xs text-gray-500 space-y-3 leading-relaxed">
                <p>
                  To compute statistics and plot figures correctly, please make sure your uploaded clinical datasets comply with the standard CDISC ADaM specifications:
                </p>
                <div className="bg-gray-50 border rounded-xl p-4 font-mono space-y-2 mt-2 overflow-x-auto text-[10px]">
                  <div className="flex justify-between border-b pb-1 text-[10px] text-gray-600 font-bold min-w-[450px]">
                    <span>Dataset Name</span>
                    <span>Required Variables</span>
                    <span>Target Report Type</span>
                  </div>
                  <div className="flex justify-between py-1 min-w-[450px]">
                    <span className="text-blue-600">adsl.sas7bdat</span>
                    <span className="text-gray-700">USUBJID, TRT01PN, TRT01P, SAFFL</span>
                    <span>All Tables / Figures / Listings</span>
                  </div>
                  <div className="flex justify-between py-1 min-w-[450px]">
                    <span className="text-blue-600">adae.sas7bdat</span>
                    <span className="text-gray-700">USUBJID, AESOC, AEDECOD, ASEQ</span>
                    <span>Table 14.3 (Adverse Events Summaries)</span>
                  </div>
                  <div className="flex justify-between py-1 min-w-[450px]">
                    <span className="text-blue-600">adtte.sas7bdat</span>
                    <span className="text-gray-700">USUBJID, PARAMCD, AVAL, CNSR</span>
                    <span>Table 14.2 / KM Survival Figures</span>
                  </div>
                  <div className="flex justify-between py-1 text-gray-400 min-w-[450px]">
                    <span>adlb/advs/adcm</span>
                    <span>USUBJID, PARAMCD, AVAL, VISIT</span>
                    <span>Laboratory / Vital Signs / Medications</span>
                  </div>
                </div>
              </div>
            </div>

            {/* FAQs */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2 border-b pb-3 mb-4">
                <HelpCircle className="h-5 w-5 text-blue-600" />
                6. Frequently Asked Questions (FAQ)
              </h2>
              <div className="space-y-4">
                {faqs.map((faq, index) => (
                  <div key={index} className="border-b last:border-0 pb-3 last:pb-0">
                    <button
                      onClick={() => toggleFaq(index)}
                      className="w-full flex justify-between items-center text-left py-2 hover:text-blue-600 transition-colors"
                    >
                      <span className="font-semibold text-gray-800 text-sm">{faq.q}</span>
                      {openFaq === index ? (
                        <ChevronUp className="h-4 w-4 text-gray-400" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-gray-400" />
                      )}
                    </button>
                    {openFaq === index && (
                      <div className="mt-2 text-xs text-gray-500 leading-relaxed pl-1 animate-in slide-in-from-top-2 duration-200">
                        {faq.a}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

          </div>

          {/* Right Sidebar Area */}
          <div className="space-y-6">
            
            {/* Contact Support Card */}
            <div id="contact-support" className="bg-white border rounded-2xl shadow-sm p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 bg-blue-500/10 p-4 rounded-bl-full text-blue-600">
                <Mail className="h-5 w-5" />
              </div>
              <h3 className="font-bold text-gray-900 text-sm">Contact Support</h3>
              <p className="text-gray-500 text-xs mt-2 leading-relaxed">
                If you encounter platform glitches, require assistance with dataset mapping, or have subscription checkout inquiries, please feel free to email our customer care team.
              </p>
              
              <div className="mt-5 space-y-3">
                <div className="bg-gray-50 rounded-lg p-3 border">
                  <div className="text-[10px] text-gray-400 font-semibold uppercase">Email Support</div>
                  <a 
                    href="mailto:info@xwqin.com" 
                    className="text-sm font-bold text-blue-600 hover:underline mt-1 block"
                  >
                    info@xwqin.com
                  </a>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-3 border">
                  <div className="text-[10px] text-gray-400 font-semibold uppercase">Response SLA</div>
                  <div className="text-xs font-bold text-gray-700 mt-1">
                    Within 24 business hours
                  </div>
                </div>
              </div>
            </div>

            {/* Platform Compliance Checklist */}
            <div className="bg-white border rounded-2xl shadow-sm p-6">
              <h3 className="font-bold text-gray-900 text-sm border-b pb-2 mb-3">SaaS Security Compliance</h3>
              <ul className="space-y-2.5 text-xs text-gray-500">
                <li className="flex items-center gap-2 font-medium">
                  <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0" />
                  Docker-Isolated Code Executions
                </li>
                <li className="flex items-center gap-2 font-medium">
                  <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0" />
                  FDA 21 CFR Part 11 Audit Trail Logs
                </li>
                <li className="flex items-center gap-2 font-medium">
                  <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0" />
                  Team Tenant Isolation & Encryption
                </li>
                <li className="flex items-center gap-2 font-medium">
                  <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0" />
                  Automated Limits & Stripe Billing
                </li>
              </ul>
            </div>

          </div>

        </div>

      </div>
    </div>
  );
}

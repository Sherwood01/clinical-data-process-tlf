"use client";

import { useEffect, useState } from "react";
import { getAccessToken } from "supertokens-web-js/recipe/session";
import { 
  Database, Search, Upload, Edit, Save, X, Loader2, Sparkles, CheckCircle, HelpCircle, FileCode, FileText
} from "lucide-react";

type Tab = "macros" | "specs" | "documents";

/**
 * 临床自适应知识库管理界面组件
 * 包含 SAS 宏程序库检索与上传、自适应变量规约调整（Adaptive Spec Tuner）、以及双轨 RAG 参考文档管理。
 */
export default function KnowledgeContent() {
  const [activeTab, setActiveTab] = useState<Tab>("macros");
  const [macros, setMacros] = useState<any[]>([]);
  const [specs, setSpecs] = useState<Record<string, any>>({});
  const [documents, setDocuments] = useState<any[]>([]);
  const [studies, setStudies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  
  // Modal states (Macros)
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [fileToUpload, setFileToUpload] = useState<File | null>(null);

  // Modal states (Documents)
  const [isDocUploadOpen, setIsDocUploadOpen] = useState(false);
  const [docUploading, setDocUploading] = useState(false);
  const [docFileToUpload, setDocFileToUpload] = useState<File | null>(null);
  const [docUploadType, setDocUploadType] = useState<"global" | "study">("study");
  const [selectedStudyId, setSelectedStudyId] = useState<string>("");
  
  const [editingSpecId, setEditingSpecId] = useState<string | null>(null);
  const [editingSpecData, setEditingSpecData] = useState<any>(null);
  const [savingSpec, setSavingSpec] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchKnowledgeData();
    fetchStudies();
    fetchDocuments();
  }, []);

  async function fetchKnowledgeData() {
    setLoading(true);
    try {
      const token = await getAccessToken();
      const headers = { Authorization: `Bearer ${token}` };

      const [macrosRes, specsRes] = await Promise.all([
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/knowledge/macros`, { headers }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/knowledge/specs`, { headers }),
      ]);

      if (macrosRes.ok) setMacros(await macrosRes.json());
      if (specsRes.ok) setSpecs(await specsRes.json());
    } catch (err) {
      console.error("Failed to fetch knowledge data:", err);
    } finally {
      setLoading(false);
    }
  }

  async function fetchStudies() {
    try {
      const token = await getAccessToken();
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/studies`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const studiesList = await res.json();
        setStudies(studiesList);
        if (studiesList.length > 0) {
          setSelectedStudyId(studiesList[0].id);
        }
      }
    } catch (e) {
      console.error("Failed to fetch studies:", e);
    }
  }

  async function fetchDocuments() {
    try {
      const token = await getAccessToken();
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/knowledge/documents`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) setDocuments(await res.json());
    } catch (e) {
      console.error("Failed to fetch documents:", e);
    }
  }

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fileToUpload) return;
    setUploading(true);
    try {
      const token = await getAccessToken();
      const formData = new FormData();
      formData.append("file", fileToUpload);

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/knowledge/macros/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (res.ok) {
        showToast(`🎉 SAS macro ${fileToUpload.name.replace(".sas", "")} has been successfully learned and indexed!`);
        setIsUploadOpen(false);
        setFileToUpload(null);
        fetchKnowledgeData();
      } else {
        const text = await res.text();
        alert(`Upload failed: ${text}`);
      }
    } catch (err: any) {
      alert(`Upload error: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleDocUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!docFileToUpload) return;
    setDocUploading(true);
    try {
      const token = await getAccessToken();
      const formData = new FormData();
      formData.append("file", docFileToUpload);
      if (docUploadType === "study" && selectedStudyId) {
        formData.append("study_id", selectedStudyId);
      }

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/knowledge/documents/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (res.ok) {
        showToast(`🎉 Document ${docFileToUpload.name} uploaded and indexed for RAG successfully!`);
        setIsDocUploadOpen(false);
        setDocFileToUpload(null);
        fetchDocuments();
      } else {
        const text = await res.text();
        alert(`Upload failed: ${text}`);
      }
    } catch (err: any) {
      alert(`Upload error: ${err.message}`);
    } finally {
      setDocUploading(false);
    }
  };

  const handleDocDelete = async (doc: any) => {
    const confirmDelete = window.confirm(`Are you sure you want to delete document '${doc.filename}'?`);
    if (!confirmDelete) return;
    
    try {
      const token = await getAccessToken();
      const url = doc.study_id
        ? `${process.env.NEXT_PUBLIC_API_URL}/knowledge/documents/${doc.filename}?study_id=${doc.study_id}`
        : `${process.env.NEXT_PUBLIC_API_URL}/knowledge/documents/${doc.filename}`;
        
      const res = await fetch(url, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        showToast(`🗑️ Document ${doc.filename} deleted successfully.`);
        fetchDocuments();
      } else {
        const text = await res.text();
        alert(`Delete failed: ${text}`);
      }
    } catch (err: any) {
      alert(`Delete error: ${err.message}`);
    }
  };

  const handleSpecEditClick = (tableId: string, spec: any) => {
    setEditingSpecId(tableId);
    setEditingSpecData({
      table_name: spec.table_name,
      analysis_set: spec.analysis_set,
      analysis_variables: spec.analysis_variables.join(", "),
      population_filter: spec.population_filter,
      group_by: spec.group_by
    });
  };

  const handleSpecSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingSpecId || !editingSpecData) return;
    setSavingSpec(true);
    try {
      const token = await getAccessToken();
      const variablesArray = editingSpecData.analysis_variables
        .split(",")
        .map((v: string) => v.trim())
        .filter((v: string) => v.length > 0);

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/knowledge/specs/${editingSpecId}`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          table_name: editingSpecData.table_name,
          analysis_set: editingSpecData.analysis_set,
          analysis_variables: variablesArray,
          population_filter: editingSpecData.population_filter,
          group_by: editingSpecData.group_by,
        }),
      });

      if (res.ok) {
        showToast(`✅ Variable spec template for Table ${editingSpecId} has been successfully tuned and saved!`);
        setEditingSpecId(null);
        setEditingSpecData(null);
        fetchKnowledgeData();
      } else {
        const text = await res.text();
        alert(`Failed to save template: ${text}`);
      }
    } catch (err: any) {
      alert(`Error saving template: ${err.message}`);
    } finally {
      setSavingSpec(false);
    }
  };

  // Filter macros
  const filteredMacros = macros.filter((macro) => {
    const matchesSearch = 
      macro.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      macro.purpose.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = 
      selectedCategory === "all" || macro.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#0a0f1d] text-slate-900 dark:text-slate-100 pb-12 transition-colors">
      {/* Toast Alert */}
      {toastMessage && (
        <div className="fixed bottom-5 right-5 z-50 flex items-center gap-2 bg-slate-900 dark:bg-[#101828] text-white px-5 py-3 rounded-xl shadow-lg border border-slate-700 dark:border-slate-800 animate-in fade-in slide-in-from-bottom-4 duration-300">
          <CheckCircle className="h-5 w-5 text-emerald-400" />
          <span className="text-sm font-semibold">{toastMessage}</span>
        </div>
      )}

      {/* Header Panel */}
      <header className="bg-white dark:bg-[#101828] border-b border-slate-200 dark:border-slate-800 shadow-xs transition-colors">
        <div className="container mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3.5">
            <div className="h-10 w-10 flex items-center justify-center rounded-xl bg-slate-100 dark:bg-slate-800 text-[#1e3a8a] dark:text-[#93c5fd] border border-slate-200 dark:border-slate-700">
              <Database className="h-5 w-5" />
            </div>
            <div>
              <h1 className="font-bold text-xl tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
                Clinical Adaptive Knowledge Base
                <Sparkles className="h-4 w-4 text-[#1e3a8a] dark:text-[#93c5fd] animate-pulse" />
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Cross-project shared SAS macros and VariableSpec adaptive tuning engine
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Tabs Menu */}
      <div className="border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-[#101828] transition-colors">
        <div className="container mx-auto px-6 flex justify-between items-center">
          <nav className="-mb-px flex gap-6">
            <button
              onClick={() => setActiveTab("macros")}
              className={`py-3.5 text-sm font-semibold border-b-2 transition-all duration-200 ${
                activeTab === "macros"
                  ? "border-[#1e3a8a] text-[#1e3a8a] dark:border-[#93c5fd] dark:text-[#93c5fd]"
                  : "border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
              }`}
            >
              SAS Macros Library ({macros.length})
            </button>
            <button
              onClick={() => setActiveTab("specs")}
              className={`py-3.5 text-sm font-semibold border-b-2 transition-all duration-200 ${
                activeTab === "specs"
                  ? "border-[#1e3a8a] text-[#1e3a8a] dark:border-[#93c5fd] dark:text-[#93c5fd]"
                  : "border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
              }`}
            >
              Adaptive Spec Tuner
            </button>
            <button
              onClick={() => setActiveTab("documents")}
              className={`py-3.5 text-sm font-semibold border-b-2 transition-all duration-200 ${
                activeTab === "documents"
                  ? "border-[#1e3a8a] text-[#1e3a8a] dark:border-[#93c5fd] dark:text-[#93c5fd]"
                  : "border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
              }`}
            >
              Reference Documents ({documents.length})
            </button>
          </nav>

          {activeTab === "macros" && (
            <button
              onClick={() => setIsUploadOpen(true)}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-[#1e3a8a] hover:bg-[#172554] dark:bg-[#1e40af] dark:hover:bg-[#1d4ed8] active:scale-[0.98] rounded-lg shadow-xs transition-all"
            >
              <Upload className="h-3.5 w-3.5" />
              Upload SAS Macro
            </button>
          )}

          {activeTab === "documents" && (
            <button
              onClick={() => setIsDocUploadOpen(true)}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-[#1e3a8a] hover:bg-[#172554] dark:bg-[#1e40af] dark:hover:bg-[#1d4ed8] active:scale-[0.98] rounded-lg shadow-xs transition-all"
            >
              <Upload className="h-3.5 w-3.5" />
              Upload Reference Document
            </button>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <main className="container mx-auto px-6 py-8">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-24 text-slate-400 gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-[#1e3a8a] dark:text-[#93c5fd]" />
            <p className="text-sm">Loading knowledge base...</p>
          </div>
        ) : (
          <>
            {/* TAB 1: MACROS */}
            {activeTab === "macros" && (
              <div className="space-y-6">
                {/* Search Bar */}
                <div className="flex flex-col md:flex-row gap-4 bg-white dark:bg-[#101828] p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs">
                  <div className="relative flex-1">
                    <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <input
                      type="text"
                      placeholder="Search SAS macros by name or description..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 text-sm bg-slate-50 dark:bg-[#070b14] border border-slate-200 dark:border-slate-800 focus:border-[#1e3a8a] dark:focus:border-[#93c5fd] focus:outline-none rounded-lg text-slate-900 dark:text-slate-100 placeholder:text-slate-400"
                    />
                  </div>
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="px-4 py-2 text-sm bg-slate-50 dark:bg-[#070b14] border border-slate-200 dark:border-slate-800 focus:border-[#1e3a8a] dark:focus:border-[#93c5fd] focus:outline-none rounded-lg text-slate-900 dark:text-slate-100"
                  >
                    <option value="all">All Categories</option>
                    <option value="descriptive_statistics">Descriptive Statistics (Descriptive)</option>
                    <option value="statistical_analysis">Statistical Analysis (Statistical)</option>
                  </select>
                </div>

                {/* Cards Grid */}
                {filteredMacros.length === 0 ? (
                  <div className="text-center py-16 text-slate-400 bg-white dark:bg-[#101828] border border-dashed border-slate-200 dark:border-slate-800 rounded-xl">
                    No SAS macros found matching the filters.
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredMacros.map((macro, idx) => (
                      <div 
                        key={idx}
                        className="bg-white dark:bg-[#101828] border border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 rounded-xl p-5 shadow-xs hover:shadow-sm transition-all flex flex-col justify-between"
                      >
                        <div>
                          <div className="flex items-center justify-between mb-3.5">
                            <span className="font-mono font-bold text-sm text-[#1e3a8a] dark:text-[#93c5fd]">
                              %{macro.name}
                            </span>
                            <span className={`px-2 py-0.5 text-[10px] font-semibold rounded-md border ${
                              macro.category === "descriptive_statistics"
                                ? "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800/60"
                                : "bg-sky-50 dark:bg-sky-950/40 text-sky-700 dark:text-sky-400 border-sky-200 dark:border-sky-800/60"
                            }`}>
                              {macro.category === "descriptive_statistics" ? "Descriptive" : "Statistical"}
                            </span>
                          </div>
                          
                          <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2 leading-relaxed mb-4" title={macro.purpose}>
                            {macro.purpose || "No purpose description available for this macro."}
                          </p>
                        </div>

                        <div className="border-t border-slate-100 dark:border-slate-800/80 pt-3.5 space-y-2 text-[11px]">
                          <div className="flex justify-between">
                            <span className="text-slate-400">Dependencies:</span>
                            <span className="font-mono text-slate-700 dark:text-slate-300 truncate max-w-[180px]">
                              {macro.called_macros.join(", ") || "None"}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400">Parameters:</span>
                            <span className="font-semibold text-slate-700 dark:text-slate-300">
                              {macro.parameters.length} params
                            </span>
                          </div>
                          {macro.applicable_tables && macro.applicable_tables.length > 0 && (
                            <div className="flex justify-between">
                              <span className="text-slate-400">Applicable Tables:</span>
                              <span className="text-[#1e3a8a] dark:text-[#93c5fd] font-semibold">
                                {macro.applicable_tables.join(", ")}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* TAB 2: SPECS */}
            {activeTab === "specs" && (
              <div className="space-y-6">
                <div className="bg-slate-100/70 dark:bg-[#070b14] border border-slate-200 dark:border-slate-800 rounded-xl p-5 text-sm text-slate-700 dark:text-slate-300 leading-relaxed flex items-start gap-3">
                  <HelpCircle className="h-5 w-5 text-[#1e3a8a] dark:text-[#93c5fd] flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-slate-900 dark:text-slate-100">What is Spec Tuner?</span>
                    <p className="mt-1 text-xs text-slate-600 dark:text-slate-400">
                      When the system encounters a new table design from the SAP document that is not hardcoded, the AI Agent will automatically infer its VariableSpec (analysis set, variables, filters, and grouping columns) based on the semantic context. You can review or adjust its structure here. Once you click &quot;Save &amp; Learn&quot;, it is saved to the knowledge base. For subsequent tasks, the AI Agent will prioritize this corrected specification!
                    </p>
                  </div>
                </div>

                <div className="bg-white dark:bg-[#101828] border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-xs transition-colors">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-50 dark:bg-[#070b14] border-b border-slate-200 dark:border-slate-800">
                      <tr>
                        <th className="text-left px-5 py-3.5 font-medium text-slate-600 dark:text-slate-400 text-xs uppercase tracking-wider">Table ID</th>
                        <th className="text-left px-5 py-3.5 font-medium text-slate-600 dark:text-slate-400 text-xs uppercase tracking-wider">Table Name</th>
                        <th className="text-left px-5 py-3.5 font-medium text-slate-600 dark:text-slate-400 text-xs uppercase tracking-wider">Analysis Set</th>
                        <th className="text-left px-5 py-3.5 font-medium text-slate-600 dark:text-slate-400 text-xs uppercase tracking-wider">Analysis Variables</th>
                        <th className="text-left px-5 py-3.5 font-medium text-slate-600 dark:text-slate-400 text-xs uppercase tracking-wider">Where Filter</th>
                        <th className="text-left px-5 py-3.5 font-medium text-slate-600 dark:text-slate-400 text-xs uppercase tracking-wider">Group By</th>
                        <th className="text-right px-5 py-3.5 font-medium text-slate-600 dark:text-slate-400 text-xs uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                      {Object.entries(specs).map(([tableId, spec]: [string, any]) => (
                        <tr key={tableId} className="hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors">
                          <td className="px-5 py-4 font-mono font-bold text-xs text-slate-900 dark:text-slate-100">{tableId}</td>
                          <td className="px-5 py-4 font-medium text-slate-700 dark:text-slate-300">{spec.table_name}</td>
                          <td className="px-5 py-4 text-xs text-slate-600 dark:text-slate-400">{spec.analysis_set}</td>
                          <td className="px-5 py-4">
                            <div className="flex flex-wrap gap-1.5">
                              {spec.analysis_variables.map((v: string) => (
                                <span key={v} className="px-1.5 py-0.5 font-mono text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded">
                                  {v}
                                </span>
                              ))}
                            </div>
                          </td>
                          <td className="px-5 py-4 font-mono text-xs text-amber-600 dark:text-amber-400">{spec.population_filter || "1=1"}</td>
                          <td className="px-5 py-4 font-mono text-xs text-slate-600 dark:text-slate-400">{spec.group_by}</td>
                          <td className="px-5 py-4 text-right">
                            <button
                              onClick={() => handleSpecEditClick(tableId, spec)}
                              className="inline-flex items-center gap-1 text-xs font-semibold text-[#1e3a8a] hover:text-[#172554] dark:text-[#93c5fd] dark:hover:text-blue-300 transition-colors"
                            >
                              <Edit className="h-3.5 w-3.5" />
                              Tune
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB 3: DOCUMENTS */}
            {activeTab === "documents" && (
              <div className="space-y-6">
                <div className="bg-slate-100/70 dark:bg-[#070b14] border border-slate-200 dark:border-slate-800 rounded-xl p-5 text-sm text-slate-700 dark:text-slate-300 leading-relaxed flex items-start gap-3">
                  <HelpCircle className="h-5 w-5 text-[#1e3a8a] dark:text-[#93c5fd] flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-slate-900 dark:text-slate-100">Dual-Track RAG Document Management</span>
                    <p className="mt-1 text-xs text-slate-600 dark:text-slate-400">
                      Upload reference documents (like guidelines, SAP drafts, or oncology definitions). 
                      <strong className="text-slate-800 dark:text-slate-200"> Global Industry Documents</strong> are accessible across all studies. 
                      <strong className="text-slate-800 dark:text-slate-200"> Study-Specific Documents</strong> are securely isolated and only retrieved when conversing within the corresponding study workspace.
                    </p>
                  </div>
                </div>

                <div className="bg-white dark:bg-[#101828] border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-xs transition-colors">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-50 dark:bg-[#070b14] border-b border-slate-200 dark:border-slate-800">
                      <tr>
                        <th className="text-left px-5 py-3.5 font-medium text-slate-600 dark:text-slate-400 text-xs uppercase tracking-wider">Document Name</th>
                        <th className="text-left px-5 py-3.5 font-medium text-slate-600 dark:text-slate-400 text-xs uppercase tracking-wider">Scope</th>
                        <th className="text-left px-5 py-3.5 font-medium text-slate-600 dark:text-slate-400 text-xs uppercase tracking-wider">Workspace Attachment</th>
                        <th className="text-left px-5 py-3.5 font-medium text-slate-600 dark:text-slate-400 text-xs uppercase tracking-wider font-bold max-w-[200px]">AI RAG Summary</th>
                        <th className="text-left px-5 py-3.5 font-medium text-slate-600 dark:text-slate-400 text-xs uppercase tracking-wider">Keywords</th>
                        <th className="text-left px-5 py-3.5 font-medium text-slate-600 dark:text-slate-400 text-xs uppercase tracking-wider">Uploaded At</th>
                        <th className="text-right px-5 py-3.5 font-medium text-slate-600 dark:text-slate-400 text-xs uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                      {documents.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="px-5 py-8 text-center text-slate-400">
                            No reference documents uploaded yet.
                          </td>
                        </tr>
                      ) : (
                        documents.map((doc, idx) => (
                          <tr key={idx} className="hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors">
                            <td className="px-5 py-4 font-medium text-slate-800 dark:text-slate-200">{doc.filename}</td>
                            <td className="px-5 py-4 text-xs font-semibold">
                              <span className={`px-2.5 py-0.5 rounded-md border ${
                                doc.study_id 
                                  ? "bg-sky-50 dark:bg-sky-950/40 text-sky-700 dark:text-sky-300 border-sky-200 dark:border-sky-800/60"
                                  : "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800/60"
                              }`}>
                                {doc.study_id ? "Study-Specific" : "Global Industry"}
                              </span>
                            </td>
                            <td className="px-5 py-4 text-xs text-slate-500 font-medium">
                              {doc.study_id 
                                ? (studies.find(s => s.id === doc.study_id)?.name || `Study (ID: ${doc.study_id.slice(0,8)})`)
                                : "Global Platform Scope"
                              }
                            </td>
                            <td className="px-5 py-4 text-xs text-slate-600 dark:text-slate-400 max-w-[200px] truncate" title={doc.summary}>
                              {doc.summary}
                            </td>
                            <td className="px-5 py-4">
                              <div className="flex flex-wrap gap-1 max-w-[120px]">
                                {doc.keywords.map((kw: string) => (
                                  <span key={kw} className="px-1.5 py-0.5 font-mono text-[9px] bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 rounded">
                                    {kw}
                                  </span>
                                ))}
                              </div>
                            </td>
                            <td className="px-5 py-4 text-xs text-slate-400 font-medium">{doc.uploaded_at}</td>
                            <td className="px-5 py-4 text-right">
                              <button
                                onClick={() => handleDocDelete(doc)}
                                className="text-xs font-bold text-rose-600 hover:text-rose-700 dark:text-rose-400 dark:hover:text-rose-300 active:scale-95 transition-all"
                              >
                                Delete
                              </button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {/* Modal 1: Upload SAS Macro */}
      {isUploadOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-md bg-white dark:bg-[#101828] p-6 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-800 scale-100 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800 pb-3 mb-4">
              <h3 className="font-bold text-lg text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                Upload SAS Macro File
                <Sparkles className="h-4 w-4 text-[#1e3a8a] dark:text-[#93c5fd]" />
              </h3>
              <button 
                onClick={() => setIsUploadOpen(false)}
                className="p-1 rounded-md text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleUploadSubmit} className="space-y-4">
              <div className="border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-xl p-8 flex flex-col items-center justify-center bg-slate-50 dark:bg-[#070b14]">
                <FileCode className="h-10 w-10 text-slate-400 mb-3 animate-pulse" />
                <span className="text-xs text-slate-500 dark:text-slate-400 mb-4 text-center">
                  Supports uploading standard SAS macro program files (.sas)
                </span>
                <input
                  type="file"
                  accept=".sas"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) setFileToUpload(file);
                  }}
                  className="hidden"
                  id="macro-file-picker"
                />
                <label 
                  htmlFor="macro-file-picker"
                  className="px-4 py-2 text-xs font-semibold border border-slate-200 dark:border-slate-700 hover:border-[#1e3a8a] text-slate-700 dark:text-slate-200 bg-white dark:bg-[#101828] hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg cursor-pointer transition-all shadow-xs"
                >
                  {fileToUpload ? "Change File" : "Select .sas File"}
                </label>
                {fileToUpload && (
                  <span className="mt-3 text-xs font-semibold text-emerald-500 font-mono">
                    Selected: {fileToUpload.name}
                  </span>
                )}
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setIsUploadOpen(false);
                    setFileToUpload(null);
                  }}
                  className="px-4 py-2 text-xs font-semibold border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 bg-white dark:bg-[#101828] hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading || !fileToUpload}
                  className="px-5 py-2 text-xs font-semibold text-white bg-[#1e3a8a] hover:bg-[#172554] dark:bg-[#1e40af] dark:hover:bg-[#1d4ed8] disabled:bg-slate-300 dark:disabled:bg-slate-800 rounded-lg shadow-xs flex items-center gap-1.5 transition-all"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      Extracting parameters via AI...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-3.5 w-3.5" />
                      Import & Learn
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal 2: Upload Custom Reference Document */}
      {isDocUploadOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-md bg-white dark:bg-[#101828] p-6 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-800 scale-100 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800 pb-3 mb-4">
              <h3 className="font-bold text-lg text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                Upload Reference Document
                <Sparkles className="h-4 w-4 text-[#1e3a8a] dark:text-[#93c5fd]" />
              </h3>
              <button 
                onClick={() => {
                  setIsDocUploadOpen(false);
                  setDocFileToUpload(null);
                }}
                className="p-1 rounded-md text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleDocUploadSubmit} className="space-y-4 text-xs font-semibold">
              <div className="space-y-1.5">
                <label className="text-slate-500 dark:text-slate-400">Scope Type</label>
                <select
                  value={docUploadType}
                  onChange={(e) => setDocUploadType(e.target.value as any)}
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-[#070b14] border border-slate-200 dark:border-slate-800 rounded-lg focus:border-[#1e3a8a] dark:focus:border-[#93c5fd] focus:outline-none text-slate-900 dark:text-slate-100"
                >
                  <option value="study">Study-Specific Reference Document</option>
                  <option value="global">Global Industry Standard (Admin Only)</option>
                </select>
              </div>

              {docUploadType === "study" && (
                <div className="space-y-1.5">
                  <label className="text-slate-500 dark:text-slate-400">Attach to Study Workspace</label>
                  <select
                    value={selectedStudyId}
                    onChange={(e) => setSelectedStudyId(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-[#070b14] border border-slate-200 dark:border-slate-800 rounded-lg focus:border-[#1e3a8a] dark:focus:border-[#93c5fd] focus:outline-none text-slate-900 dark:text-slate-100"
                  >
                    {studies.length === 0 ? (
                      <option value="">No studies found</option>
                    ) : (
                      studies.map(s => (
                        <option key={s.id} value={s.id}>{s.name}</option>
                      ))
                    )}
                  </select>
                </div>
              )}

              <div className="border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-xl p-6 flex flex-col items-center justify-center bg-slate-50 dark:bg-[#070b14]">
                <FileText className="h-10 w-10 text-slate-400 mb-3 animate-pulse" />
                <span className="text-[11px] text-slate-500 dark:text-slate-400 mb-4 text-center">
                  Supports PDF, TXT or Word guideline documents for RAG Q&A
                </span>
                <input
                  type="file"
                  accept=".pdf,.txt,.docx"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) setDocFileToUpload(file);
                  }}
                  className="hidden"
                  id="doc-file-picker"
                />
                <label 
                  htmlFor="doc-file-picker"
                  className="px-4 py-2 text-xs font-semibold border border-slate-200 dark:border-slate-700 hover:border-[#1e3a8a] text-slate-700 dark:text-slate-200 bg-white dark:bg-[#101828] hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg cursor-pointer transition-all shadow-xs"
                >
                  {docFileToUpload ? "Change File" : "Select Document File"}
                </label>
                {docFileToUpload && (
                  <span className="mt-3 text-xs font-semibold text-emerald-500 font-mono text-center max-w-[280px] truncate">
                    Selected: {docFileToUpload.name}
                  </span>
                )}
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => {
                    setIsDocUploadOpen(false);
                    setDocFileToUpload(null);
                  }}
                  className="px-4 py-2 text-slate-700 dark:text-slate-300 bg-white dark:bg-[#101828] border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={docUploading || !docFileToUpload}
                  className="px-5 py-2 text-white bg-[#1e3a8a] hover:bg-[#172554] dark:bg-[#1e40af] dark:hover:bg-[#1d4ed8] disabled:bg-slate-300 dark:disabled:bg-slate-800 rounded-lg shadow-xs flex items-center gap-1.5 transition-all"
                >
                  {docUploading ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      Summarizing & Indexing via AI...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-3.5 w-3.5" />
                      Upload & Learn
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal 3: Tune Spec Table Form */}
      {editingSpecId && editingSpecData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-lg bg-white dark:bg-[#101828] p-6 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-800 scale-100 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800 pb-3 mb-4">
              <h3 className="font-bold text-lg text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                Tune VariableSpec Template for Table {editingSpecId}
                <Sparkles className="h-4 w-4 text-amber-500" />
              </h3>
              <button 
                onClick={() => {
                  setEditingSpecId(null);
                  setEditingSpecData(null);
                }}
                className="p-1 rounded-md text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSpecSave} className="space-y-4 text-xs font-semibold">
              <div className="space-y-1">
                <label className="text-slate-500 dark:text-slate-400">Table Name</label>
                <input
                  type="text"
                  value={editingSpecData.table_name}
                  onChange={(e) => setEditingSpecData({ ...editingSpecData, table_name: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-[#070b14] border border-slate-200 dark:border-slate-800 rounded-lg focus:border-[#1e3a8a] dark:focus:border-[#93c5fd] focus:outline-none text-slate-900 dark:text-slate-100"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-500 dark:text-slate-400">Analysis Population</label>
                <input
                  type="text"
                  value={editingSpecData.analysis_set}
                  onChange={(e) => setEditingSpecData({ ...editingSpecData, analysis_set: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-[#070b14] border border-slate-200 dark:border-slate-800 rounded-lg focus:border-[#1e3a8a] dark:focus:border-[#93c5fd] focus:outline-none text-slate-900 dark:text-slate-100"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-500 dark:text-slate-400">Analysis Variables (comma-separated, e.g. AVAL, CHG)</label>
                <input
                  type="text"
                  value={editingSpecData.analysis_variables}
                  onChange={(e) => setEditingSpecData({ ...editingSpecData, analysis_variables: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-[#070b14] border border-slate-200 dark:border-slate-800 font-mono rounded-lg focus:border-[#1e3a8a] dark:focus:border-[#93c5fd] focus:outline-none text-slate-900 dark:text-slate-100"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-500 dark:text-slate-400">Where Filter (e.g. SAFFL=&apos;Y&apos;)</label>
                <input
                  type="text"
                  value={editingSpecData.population_filter}
                  onChange={(e) => setEditingSpecData({ ...editingSpecData, population_filter: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-[#070b14] border border-slate-200 dark:border-slate-800 font-mono rounded-lg focus:border-[#1e3a8a] dark:focus:border-[#93c5fd] focus:outline-none text-slate-900 dark:text-slate-100"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-500 dark:text-slate-400">Group By Variable (e.g. TRTA)</label>
                <input
                  type="text"
                  value={editingSpecData.group_by}
                  onChange={(e) => setEditingSpecData({ ...editingSpecData, group_by: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-[#070b14] border border-slate-200 dark:border-slate-800 font-mono rounded-lg focus:border-[#1e3a8a] dark:focus:border-[#93c5fd] focus:outline-none text-slate-900 dark:text-slate-100"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => {
                    setEditingSpecId(null);
                    setEditingSpecData(null);
                  }}
                  className="px-4 py-2 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 bg-white dark:bg-[#101828] hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg font-semibold transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingSpec}
                  className="px-5 py-2 text-white bg-[#1e3a8a] hover:bg-[#172554] dark:bg-[#1e40af] dark:hover:bg-[#1d4ed8] disabled:bg-slate-300 dark:disabled:bg-slate-800 rounded-lg shadow-xs font-semibold flex items-center gap-1.5 transition-all"
                >
                  {savingSpec ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Save className="h-3.5 w-3.5" />
                  )}
                  Save & Learn
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

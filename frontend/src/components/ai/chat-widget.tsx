"use client";

import { useEffect, useRef, useState } from "react";
import {
  MessageSquare,
  X,
  Send,
  Loader2,
  Sparkles,
  FileText,
  CheckCircle2,
  ChevronRight,
  HelpCircle,
  Trash2,
  History,
  Plus,
  Edit3,
  MessageCircle,
  Cpu,
  AlertTriangle,
  Square
} from "lucide-react";

interface ChatWidgetProps {
  studyId: string;
  tenantId: string;
  userId: string;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  status?: string; // e.g. "thinking" | "executing_tool" | "mode_switch_required"
  toolName?: string;
  customFigure?: {
    success: boolean;
    downloadUrl?: string;
    stdout?: string;
    error?: string;
  };
}

interface ChatSession {
  id: string;
  title: string;
  studyId: string;
  studyName?: string;
  updatedAt: number;
}

/**
 * 临床 AI Agent 悬浮对话浮窗组件。
 * 提供自然语言交互、多模型切换（GLM、DeepSeek 等）、沙箱代码执行与报告预览、以及工作/对话双模式支持。
 */
export function ChatWidget({ studyId, tenantId, userId }: ChatWidgetProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [currentStatus, setCurrentStatus] = useState<string>("idle");
  const [executingToolName, setExecutingToolName] = useState<string>("");

  // History session management states (PostgreSQL Backed)
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);

  // New Work Modes and Model togglers
  const [chatMode, setChatMode] = useState<"chat" | "work">("work");
  const [chatModel, setChatModel] = useState<string>("@cf/zai-org/glm-4.7-flash");
  const [showModelDropdown, setShowModelDropdown] = useState(false);

  // Slash commands popup suggestion states
  const [showSlashMenu, setShowSlashMenu] = useState(false);
  const [slashSelectedIndex, setSlashSelectedIndex] = useState(0);

  const scrollRef = useRef<HTMLDivElement>(null);

  const modelOptions = [
    { name: "@cf/zai-org/glm-4.7-flash", label: "🌐 CF Workers AI (GLM 4.7 Flash)" },
    { name: "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b", label: "🧠 CF Workers AI (DeepSeek R1 32B)" },
    { name: "@cf/meta/llama-3.1-8b-instruct-fp8", label: "⚡️ CF Workers AI (Llama 3.1 8B)" },
    { name: "@cf/meta/llama-3.3-70b-instruct-fp8-fast", label: "💻 CF Workers AI (Llama 3.3 70B)" },
    { name: "deepseek-v4-flash", label: "⚡️ DeepSeek V4 Flash (Direct)" },
    { name: "Opus-4.6", label: "🧠 Opus-4.6" },
    { name: "Gemini-3.5", label: "✨ Gemini-3.5" },
    { name: "GPT-5.5", label: "🚀 GPT-5.5" }
  ];

  const slashCommands = [
    { name: "/chat", label: "Switch to Chat Mode", desc: "QA and local manual search only" },
    { name: "/work", label: "Switch to Work Mode", desc: "Allows database and assets mutations" }
  ];

  const getApiUrl = () => {
    if (typeof window !== "undefined") {
      return process.env.NEXT_PUBLIC_API_URL || "/api/v1";
    }
    return "/api/v1";
  };

  // Fetch sessions list belonging to active study from DB
  const loadSessions = async (forceSelectFirst = false) => {
    try {
      const res = await fetch(`${getApiUrl()}/ai/chat/sessions`);
      if (res.ok) {
        const data = await res.json();
        const mappedSessions: ChatSession[] = data.map((s: any) => ({
          id: s.id,
          title: s.title,
          studyId: s.study_id,
          studyName: s.study_name,
          updatedAt: s.updated_at
        }));

        setSessions(mappedSessions);

        if (mappedSessions.length > 0) {
          if (forceSelectFirst || !activeSessionId || !mappedSessions.some(s => s.id === activeSessionId)) {
            const match = mappedSessions.find((s) => s.studyId === studyId);
            if (match) {
              setActiveSessionId(match.id);
            } else {
              setActiveSessionId(mappedSessions[0].id);
            }
          }
        } else {
          if (studyId) {
            await handleNewChat();
          }
        }
      }
    } catch (e) {
      console.error("Failed to load chat sessions from backend DB:", e);
    }
  };

  // Pull sessions list on load or user switch
  useEffect(() => {
    if (userId) {
      loadSessions(true);
    }
  }, [userId]);

  // Align activeSessionId context when studyId changes manually (sidebar menu)
  useEffect(() => {
    if (!studyId || sessions.length === 0 || !activeSessionId) return;
    const currentActiveSession = sessions.find((s) => s.id === activeSessionId);

    if (currentActiveSession && currentActiveSession.studyId !== studyId) {
      const match = sessions
        .filter((s) => s.studyId === studyId)
        .sort((a, b) => b.updatedAt - a.updatedAt)[0];

      if (match) {
        setActiveSessionId(match.id);
      } else {
        handleNewChat();
      }
    }
  }, [studyId, sessions]);

  // Fetch message log for the active session
  useEffect(() => {
    if (!activeSessionId) return;
    const loadMessages = async () => {
      try {
        const res = await fetch(`${getApiUrl()}/ai/chat/sessions/${activeSessionId}/messages`);
        if (res.ok) {
          const data = await res.json();
          setMessages(data);
        }
      } catch (e) {
        console.error("Failed to load messages for session:", activeSessionId, e);
      }
    };
    loadMessages();
  }, [activeSessionId]);

  // Create a brand new session thread
  const handleNewChat = async () => {
    if (!studyId) return;
    try {
      const res = await fetch(`${getApiUrl()}/ai/chat/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ study_id: studyId, title: "New Chat" })
      });
      if (res.ok) {
        const newSessionRaw = await res.json();
        const newSession: ChatSession = {
          id: newSessionRaw.id,
          title: newSessionRaw.title,
          studyId: newSessionRaw.study_id,
          updatedAt: newSessionRaw.updated_at
        };

        setSessions((prev) => [newSession, ...prev]);
        setActiveSessionId(newSession.id);
        setShowHistory(false);
      }
    } catch (e) {
      console.error("Failed to create new chat session in DB:", e);
    }
  };

  // Rename session
  const handleRenameSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const sessionToRename = sessions.find((s) => s.id === sessionId);
    if (!sessionToRename) return;
    const newTitle = prompt("Enter new title for this conversation:", sessionToRename.title);
    if (newTitle && newTitle.trim()) {
      try {
        const res = await fetch(`${getApiUrl()}/ai/chat/sessions/${sessionId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: newTitle.trim() })
        });
        if (res.ok) {
          setSessions((prev) =>
            prev.map((s) => (s.id === sessionId ? { ...s, title: newTitle.trim() } : s))
          );
        }
      } catch (e) {
        console.error("Failed to rename session:", e);
      }
    }
  };

  // Delete session
  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this chat session?")) return;
    try {
      const res = await fetch(`${getApiUrl()}/ai/chat/sessions/${sessionId}`, {
        method: "DELETE"
      });
      if (res.ok) {
        const updatedList = sessions.filter((s) => s.id !== sessionId);
        setSessions(updatedList);

        if (activeSessionId === sessionId) {
          if (updatedList.length > 0) {
            setActiveSessionId(updatedList[0].id);
          } else {
            await handleNewChat();
          }
        }
      }
    } catch (e) {
      console.error("Failed to delete session:", e);
    }
  };

  // Reset conversation
  const handleClearHistory = async () => {
    if (!activeSessionId) return;
    if (confirm("Are you sure you want to reset this conversation? This will clear this thread and start a fresh chat.")) {
      try {
        const res = await fetch(`${getApiUrl()}/ai/chat/sessions/${activeSessionId}`, {
          method: "DELETE"
        });
        if (res.ok) {
          await handleNewChat();
        }
      } catch (e) {
        console.error("Failed to reset conversation:", e);
      }
    }
  };

  // Switch and execute command triggered by safe interception
  const handleSwitchAndExecute = () => {
    setChatMode("work");
    // Find last user input message
    const userMsgs = messages.filter((m) => m.role === "user");
    if (userMsgs.length > 0) {
      const lastUserQuery = userMsgs[userMsgs.length - 1].content;
      if (ws && connected) {
        ws.send(JSON.stringify({
          message: lastUserQuery,
          mode: "work",
          model: chatModel
        }));
        setMessages((prev) => [
          ...prev,
          { role: "user", content: lastUserQuery },
          { role: "assistant", content: `🔄 Switched to Work Mode. Executing: "${lastUserQuery}"...` }
        ]);
      }
    }
  };

  // Establish WebSocket connection when opened or active session changes
  useEffect(() => {
    if (!isOpen || !activeSessionId) {
      if (ws) {
        ws.close();
      }
      return;
    }

    if (!studyId) {
      setConnected(false);
      setMessages([
        {
          role: "assistant",
          content: "Hello! I am your Clinical TLF AI Agent.\n\nIt looks like you haven't opened or created a study yet. Please navigate to **Studies** in the left sidebar to enter or create a study, and I will be here to help you run reports, generate charts, and answer questions."
        }
      ]);
      return;
    }

    if (!tenantId || !userId) {
      setConnected(false);
      logger_info("WS waiting for session credentials to resolve...");
      return;
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    let wsHost = "";
    if (typeof window !== "undefined") {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "";
      if (apiUrl.startsWith("http://") || apiUrl.startsWith("https://")) {
        wsHost = apiUrl.replace("http://", "").replace("https://", "");
      } else {
        wsHost = window.location.host;
      }
    }

    const wsUrl = `${protocol}//${wsHost}/api/v1/ai/chat/ws?study_id=${studyId}`;

    logger_info("Connecting to AI Chat WS: " + wsUrl);
    const socket = new WebSocket(wsUrl);

    socket.onerror = (err) => {
      console.error("WebSocket connection error:", err);
    };

    socket.onopen = () => {
      setConnected(true);
      socket.send(
        JSON.stringify({
          type: "auth",
          tenant_id: tenantId,
          user_id: userId,
          session_id: activeSessionId
        })
      );
    };

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);

        if (payload.type === "text") {
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last && last.role === "assistant" && !last.customFigure && last.status !== "mode_switch_required") {
              return [
                ...prev.slice(0, -1),
                { ...last, content: last.content + payload.content }
              ];
            } else {
              return [...prev, { role: "assistant", content: payload.content }];
            }
          });
        }

        else if (payload.type === "mode_switch_prompt") {
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: "⚠️ This action requires Work Mode to execute. Would you like to switch to Work Mode now?",
              status: "mode_switch_required"
            }
          ]);
        }

        else if (payload.type === "status") {
          setCurrentStatus(payload.status);
          if (payload.status === "executing_tool") {
            setExecutingToolName(payload.tool || "");
          } else {
            setExecutingToolName("");
          }
        }

        else if (payload.type === "action") {
          if (payload.action === "switch_study") {
            window.location.href = `/studies/${payload.study_id}`;
          }
        }

        else if (payload.type === "custom_figure_result") {
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: payload.message || "Sandbox run complete.",
              customFigure: {
                success: payload.success,
                downloadUrl: payload.download_url,
                stdout: payload.stdout,
                error: payload.error,
              }
            }
          ]);
        }

        else if (payload.type === "error") {
          setMessages((prev) => [
            ...prev,
            { role: "assistant", content: `❌ Error: ${payload.message}` }
          ]);
        }
      } catch (err) {
        console.error("Failed to parse WS message:", err);
      }
    };

    socket.onclose = () => {
      setConnected(false);
      setCurrentStatus("idle");
    };

    setWs(socket);

    return () => {
      socket.close();
    };
  }, [isOpen, studyId, tenantId, userId, activeSessionId]);

  const scrollToBottom = (behavior: ScrollBehavior = "smooth") => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior
      });
    }
  };

  // Auto scroll to bottom when messages update, status changes, panel opens, or history view toggles
  useEffect(() => {
    if (isOpen && !showHistory) {
      const timer = setTimeout(() => {
        scrollToBottom(messages.length <= 2 ? "instant" : "smooth");
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [messages, currentStatus, isOpen, showHistory]);

  const handleSend = () => {
    if (!inputValue.trim() || !ws || !connected) return;

    ws.send(JSON.stringify({
      message: inputValue,
      mode: chatMode,
      model: chatModel
    }));

    setMessages((prev) => [...prev, { role: "user", content: inputValue }]);

    // Auto title naming
    setSessions((prev) =>
      prev.map((s) => {
        if (s.id === activeSessionId && s.title === "New Chat") {
          const titleCandidate = inputValue.trim();
          const newTitle = titleCandidate.length > 25
            ? titleCandidate.substring(0, 22) + "..."
            : titleCandidate;
          return { ...s, title: newTitle };
        }
        return s;
      })
    );

    setInputValue("");
  };

  const handleAbort = () => {
    if (ws && connected) {
      ws.send(JSON.stringify({ type: "abort" }));
    }
    setCurrentStatus("idle");
    setExecutingToolName("");
    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: "⏹️ **Generation forcefully stopped by user.**" }
    ]);
  };

  const handleQuickAction = (text: string) => {
    if (!ws || !connected) return;
    ws.send(JSON.stringify({
      message: text,
      mode: chatMode,
      model: chatModel
    }));

    setMessages((prev) => [...prev, { role: "user", content: text }]);

    setSessions((prev) =>
      prev.map((s) => {
        if (s.id === activeSessionId && s.title === "New Chat") {
          const titleCandidate = text.trim();
          const newTitle = titleCandidate.length > 25
            ? titleCandidate.substring(0, 22) + "..."
            : titleCandidate;
          return { ...s, title: newTitle };
        }
        return s;
      })
    );
  };

  const handleInputChange = (val: string) => {
    setInputValue(val);
    if (val.startsWith("/")) {
      setShowSlashMenu(true);
      setSlashSelectedIndex(0);
    } else {
      setShowSlashMenu(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (showSlashMenu) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSlashSelectedIndex((prev) => (prev + 1) % slashCommands.length);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSlashSelectedIndex((prev) => (prev - 1 + slashCommands.length) % slashCommands.length);
      } else if (e.key === "Enter") {
        e.preventDefault();
        selectSlashCommand(slashCommands[slashSelectedIndex].name);
      } else if (e.key === "Escape") {
        setShowSlashMenu(false);
      }
    } else {
      if (e.key === "Enter") {
        handleSend();
      }
    }
  };

  const selectSlashCommand = (cmd: string) => {
    if (cmd === "/chat") {
      setChatMode("chat");
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "🔄 Switched active work mode to **Chat Mode** (Safe & Read-only)." }
      ]);
    } else if (cmd === "/work") {
      setChatMode("work");
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "🔄 Switched active work mode to **Work Mode** (Action Agent operational)." }
      ]);
    }
    setInputValue("");
    setShowSlashMenu(false);
  };

  function logger_info(msg: string) {
    console.log("[AI Agent Widget]", msg);
  }

  const quickActions = [
    { text: "How do I upload ADaM datasets?", icon: HelpCircle },
    { text: "Generate Table 14.1.1.1", icon: Sparkles },
    { text: "Draw a KM OS survival curve", icon: FileText }
  ];

  return (
    <>
      {/* Floating Chat Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed right-6 bottom-6 px-5 h-13 bg-[#1e3a8a] hover:bg-[#172554] dark:bg-[#1e40af] dark:hover:bg-[#1d4ed8] text-white shadow-lg hover:shadow-xl hover:scale-105 active:scale-95 transition-all duration-200 z-40 flex items-center justify-center gap-2 rounded-full group border border-slate-700/30 dark:border-slate-700"
        title="Open AI Clinical Agent"
      >
        {isOpen ? (
          <>
            <X className="h-5 w-5 animate-in spin-in-90 duration-200" />
            <span className="text-[10px] font-bold uppercase tracking-wider">Close</span>
          </>
        ) : (
          <div className="flex items-center gap-2">
            <div className="relative flex items-center justify-center">
              <Sparkles className="h-4.5 w-4.5 text-[#93c5fd] animate-pulse" />
              <span className="absolute -top-1 -right-1 flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sky-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-sky-300"></span>
              </span>
            </div>
            <span className="text-xs font-black uppercase tracking-widest text-white">
              AI Agent
            </span>
          </div>
        )}
      </button>

      {/* Conversation Panel */}
      {isOpen && (
        <div className="fixed right-6 bottom-24 w-[380px] h-[520px] bg-white dark:bg-[#101828] border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl flex flex-col z-40 animate-in fade-in slide-in-from-bottom-5 duration-200 overflow-hidden transition-colors">

          {/* Header */}
          <div className="px-5 py-4 border-b border-slate-200/80 dark:border-slate-800 bg-[#1e3a8a] dark:bg-[#070b14] text-white flex justify-between items-center shrink-0">
            <div className="flex items-center gap-2">
              <div className="bg-white/10 dark:bg-slate-800/80 p-1.5 rounded-lg border border-white/10 dark:border-slate-700">
                <Sparkles className="h-4 w-4 text-[#93c5fd] animate-pulse" />
              </div>
              <div>
                <h3 className="font-bold text-sm leading-tight">Clinical AI Agent</h3>
                <p className="text-[10px] text-slate-300 dark:text-slate-400 mt-0.5">
                  {connected ? `● Connected (${chatMode === "work" ? "Work Mode" : "Chat Mode"})` : "○ Disconnected"}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={() => {
                  setShowHistory(!showHistory);
                  if (!showHistory) {
                    loadSessions(false);
                  }
                }}
                className={`text-white/70 hover:text-white hover:bg-white/10 p-1.5 rounded-lg transition-colors ${showHistory ? "bg-white/20 text-white" : ""}`}
                title="Chat History"
              >
                <History className="h-4 w-4" />
              </button>
              {messages.length > 1 && !showHistory && (
                <button
                  onClick={handleClearHistory}
                  className="text-white/70 hover:text-white hover:bg-white/10 p-1.5 rounded-lg transition-colors"
                  title="Clear conversation history"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              )}
              <button
                onClick={() => setIsOpen(false)}
                className="text-white/70 hover:text-white hover:bg-white/10 p-1.5 rounded-lg transition-colors"
                title="Close panel"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Conditional Views Layout */}
          {showHistory ? (
            <div className="flex-1 flex flex-col bg-slate-50 dark:bg-[#0a0f1d] overflow-hidden">
              {/* Recent Chats Action Bar */}
              <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-[#101828] flex justify-between items-center shrink-0">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest pl-1 font-sans">Recent Chats</span>
                <button
                  onClick={handleNewChat}
                  className="flex items-center gap-1 bg-[#1e3a8a] hover:bg-[#172554] dark:bg-[#1e40af] dark:hover:bg-[#1d4ed8] text-white px-2.5 py-1.5 rounded-lg font-bold text-[10px] uppercase tracking-wider transition-colors shadow-xs"
                >
                  <Plus className="h-3.5 w-3.5" />
                  New Chat
                </button>
              </div>

              {/* Sessions List */}
              <div className="flex-1 overflow-y-auto p-4 space-y-2">
                {sessions.length === 0 ? (
                  <div className="text-center py-12 text-slate-400 text-xs font-medium">
                    No recent chats.
                  </div>
                ) : (
                  sessions
                    .map((s) => (
                      <div
                        key={s.id}
                        onClick={() => {
                          setActiveSessionId(s.id);
                          setShowHistory(false);
                          if (s.studyId !== studyId) {
                            window.location.href = `/studies/${s.studyId}`;
                          }
                        }}
                        className={`group flex items-center justify-between p-3 rounded-xl border text-xs cursor-pointer transition-all ${activeSessionId === s.id
                          ? "bg-slate-100 dark:bg-slate-800/80 border-slate-300 dark:border-slate-700 text-[#1e3a8a] dark:text-[#93c5fd] font-bold"
                          : "bg-white dark:bg-[#101828] border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50 text-slate-700 dark:text-slate-300"
                          }`}
                      >
                        <div className="flex flex-col gap-0.5 truncate max-w-[75%]">
                          <div className="flex items-center gap-2 truncate">
                            <MessageCircle className={`h-4 w-4 shrink-0 ${activeSessionId === s.id ? "text-[#1e3a8a] dark:text-[#93c5fd]" : "text-slate-400"}`} />
                            <span className="truncate">{s.title}</span>
                          </div>
                          {s.studyName && (
                            <span className="text-[9px] text-slate-400 pl-6 truncate font-sans">
                              Study: {s.studyName}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                          <button
                            onClick={(e) => handleRenameSession(s.id, e)}
                            className="p-1 rounded text-slate-400 hover:text-[#1e3a8a] dark:hover:text-[#93c5fd] hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                            title="Rename chat"
                          >
                            <Edit3 className="h-3.5 w-3.5" />
                          </button>
                          <button
                            onClick={(e) => handleDeleteSession(s.id, e)}
                            className="p-1 rounded text-slate-400 hover:text-rose-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                            title="Delete chat"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </div>
                    ))
                )}
              </div>

              {/* Back to active chat */}
              <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-[#101828] flex justify-center shrink-0">
                <button
                  onClick={() => setShowHistory(false)}
                  className="text-xs font-semibold text-[#1e3a8a] dark:text-[#93c5fd] hover:underline transition-colors"
                >
                  Back to active chat
                </button>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Messages Flow Area */}
              <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/60 dark:bg-[#0a0f1d]"
              >
                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"
                      }`}
                  >
                    {/* Message Bubble */}
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-xs shadow-xs leading-relaxed whitespace-pre-wrap ${msg.role === "user"
                        ? "bg-[#1e3a8a] dark:bg-[#1e40af] text-white rounded-br-none"
                        : "bg-white dark:bg-[#101828] border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200 rounded-bl-none shadow-xs"
                        }`}
                    >
                      {msg.content}
                    </div>

                    {/* Mode Promotion Switch Card */}
                    {msg.status === "mode_switch_required" && (
                      <div className="w-[85%] border rounded-xl bg-amber-50/80 dark:bg-amber-950/20 p-4 shadow-xs border-amber-200 dark:border-amber-800/60 mt-2 space-y-3 animate-in zoom-in-95">
                        <div className="flex items-start gap-2.5 text-amber-800 dark:text-amber-300 text-xs leading-snug">
                          <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                          <div>
                            <span className="font-bold block text-amber-900 dark:text-amber-200">Work Action Blocked</span>
                            This command executes changes to your project. Switch to Work Mode to run it.
                          </div>
                        </div>
                        <button
                          onClick={handleSwitchAndExecute}
                          className="w-full flex items-center justify-center gap-1.5 bg-[#1e3a8a] hover:bg-[#172554] dark:bg-[#1e40af] dark:hover:bg-[#1d4ed8] text-white rounded-lg py-2 font-bold text-xs shadow-xs transition-all"
                        >
                          <Sparkles className="h-3.5 w-3.5 text-[#93c5fd]" />
                          Switch to Work Mode &amp; Execute
                        </button>
                      </div>
                    )}

                    {/* Custom Figure Download Card */}
                    {msg.customFigure && msg.customFigure.success && (
                      <div className="w-[85%] border rounded-xl bg-white dark:bg-[#101828] p-3 shadow-xs border-emerald-200 dark:border-emerald-800/60 mt-2 space-y-2 animate-in zoom-in-95">
                        <div className="flex items-center gap-1.5 text-emerald-700 dark:text-emerald-400 font-bold text-xs">
                          <CheckCircle2 className="h-4 w-4" />
                          Chart Generated Successfully (Persistent)
                        </div>
                        {msg.customFigure.stdout && (
                          <pre className="text-[10px] bg-slate-900 text-slate-300 p-2 rounded max-h-[80px] overflow-auto font-mono">
                            {msg.customFigure.stdout}
                          </pre>
                        )}
                        {msg.customFigure.downloadUrl && (
                          <a
                            href={msg.customFigure.downloadUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="flex items-center justify-center gap-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg py-1.5 font-semibold text-xs transition-all w-full text-center shadow-xs"
                          >
                            <FileText className="h-3.5 w-3.5" />
                            Preview &amp; Download PDF Report
                          </a>
                        )}
                      </div>
                    )}
                  </div>
                ))}

                {/* Quick action buttons in the first step */}
                {messages.length <= 1 && (
                  <div className="space-y-2 pt-2">
                    <p className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider pl-1 font-sans">
                      Quick Actions
                    </p>
                    <div className="flex flex-col gap-1.5">
                      {quickActions.map((qa, i) => {
                        const Icon = qa.icon;
                        return (
                          <button
                            key={i}
                            onClick={() => handleQuickAction(qa.text)}
                            className="flex items-center gap-2 text-left bg-white dark:bg-[#101828] border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50 hover:border-slate-300 dark:hover:border-slate-700 text-slate-700 dark:text-slate-300 text-xs px-3.5 py-2 rounded-xl transition-all shadow-xs"
                          >
                            <Icon className="h-3.5 w-3.5 text-[#1e3a8a] dark:text-[#93c5fd] shrink-0" />
                            <span className="truncate">{qa.text}</span>
                            <ChevronRight className="h-3 w-3 text-slate-300 dark:text-slate-600 ml-auto shrink-0" />
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Dynamically Glowing Status indicator */}
                {(currentStatus === "thinking" || currentStatus === "executing_tool") && (
                  <div className="flex items-center gap-2 pl-2 py-1 text-slate-400 animate-pulse text-[11px] font-medium shrink-0">
                    <Loader2 className="h-3.5 w-3.5 animate-spin text-[#1e3a8a] dark:text-[#93c5fd]" />
                    {currentStatus === "thinking" && "AI is thinking..."}
                    {currentStatus === "executing_tool" && (
                      <span>
                        Executing tool:{" "}
                        <span className="font-mono text-[#1e3a8a] dark:text-[#93c5fd] bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 px-1 py-0.5 rounded text-[10px]">
                          {executingToolName}
                        </span>
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Input Area Wrapper */}
              <div className="border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-[#101828] flex flex-col shrink-0 relative transition-colors">

                {/* Slash commands suggestions overlay */}
                {showSlashMenu && (
                  <div className="absolute left-3 right-3 bottom-full mb-2 bg-white dark:bg-[#101828] border border-slate-200 dark:border-slate-800 rounded-xl shadow-2xl p-1.5 z-50 animate-in fade-in slide-in-from-bottom-3 duration-150">
                    <div className="px-2 py-1 border-b border-slate-100 dark:border-slate-800 mb-1 flex items-center justify-between">
                      <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">Switch Mode</span>
                      <span className="text-[8px] text-slate-400 bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded font-mono">Use ↑↓ and Enter</span>
                    </div>
                    {slashCommands.map((cmd, idx) => (
                      <button
                        key={cmd.name}
                        onClick={() => selectSlashCommand(cmd.name)}
                        className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-colors flex items-center justify-between ${slashSelectedIndex === idx
                          ? "bg-[#1e3a8a] dark:bg-[#1e40af] text-white font-bold"
                          : "text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                          }`}
                      >
                        <div className="flex flex-col text-left">
                          <span className="font-bold">{cmd.name}</span>
                          <span className={`text-[9px] mt-0.5 ${slashSelectedIndex === idx ? "text-slate-200" : "text-slate-400"}`}>
                            {cmd.desc}
                          </span>
                        </div>
                        <ChevronRight className={`h-3 w-3 ${slashSelectedIndex === idx ? "text-white" : "text-slate-400"}`} />
                      </button>
                    ))}
                  </div>
                )}

                {/* Main text input block */}
                <div className="p-3 flex items-center gap-2">
                  <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => handleInputChange(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        if (currentStatus === "thinking" || currentStatus === "executing_tool") {
                          handleAbort();
                        } else {
                          handleSend();
                        }
                      }
                    }}
                    placeholder={!studyId ? "Open or create a study to start chatting..." : connected ? "Ask me anything (type '/' for modes)..." : "Connecting to AI Agent..."}
                    disabled={!studyId || !connected}
                    className="flex-1 bg-slate-50 dark:bg-[#070b14] border border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 focus:border-[#1e3a8a] dark:focus:border-[#93c5fd] outline-none rounded-lg px-3 py-2 text-xs text-slate-900 dark:text-slate-100 placeholder:text-slate-400 transition-colors disabled:opacity-50 disabled:bg-slate-100 dark:disabled:bg-slate-900"
                  />
                  {currentStatus === "thinking" || currentStatus === "executing_tool" ? (
                    <button
                      onClick={handleAbort}
                      title="Stop generation"
                      className="h-8 w-8 rounded-lg bg-rose-500 hover:bg-rose-600 text-white flex items-center justify-center transition-colors shrink-0 shadow-xs animate-pulse"
                    >
                      <Square className="h-3.5 w-3.5 fill-current" />
                    </button>
                  ) : (
                    <button
                      onClick={handleSend}
                      disabled={!connected || !inputValue.trim()}
                      title="Send message"
                      className="h-8 w-8 rounded-lg bg-[#1e3a8a] hover:bg-[#172554] dark:bg-[#1e40af] dark:hover:bg-[#1d4ed8] text-white flex items-center justify-center disabled:bg-slate-200 dark:disabled:bg-slate-800 disabled:text-slate-400 transition-colors shrink-0 shadow-xs"
                    >
                      <Send className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>

                {/* Controls Ribbon */}
                <div className="px-3 py-2 border-t border-slate-200 dark:border-slate-800 bg-slate-50/80 dark:bg-[#070b14] flex items-center justify-between shrink-0 select-none">
                  {/* Mode Sliding capsule Toggler */}
                  <div className="flex items-center bg-slate-200/80 dark:bg-slate-800 p-0.5 rounded-lg border border-slate-300/40 dark:border-slate-700">
                    <button
                      onClick={() => {
                        setChatMode("chat");
                        setMessages((prev) => [
                          ...prev,
                          { role: "assistant", content: "🔄 Switched active work mode to **Chat Mode** (Safe & Read-only)." }
                        ]);
                      }}
                      className={`px-2.5 py-1 rounded-md text-[9px] font-black uppercase tracking-wider flex items-center gap-1 transition-all ${chatMode === "chat"
                        ? "bg-white dark:bg-[#101828] text-[#1e3a8a] dark:text-[#93c5fd] shadow-xs font-extrabold"
                        : "text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
                        }`}
                    >
                      <MessageCircle className="h-3 w-3" />
                      Chat
                    </button>
                    <button
                      onClick={() => {
                        setChatMode("work");
                        setMessages((prev) => [
                          ...prev,
                          { role: "assistant", content: "🔄 Switched active work mode to **Work Mode** (Action Agent operational)." }
                        ]);
                      }}
                      className={`px-2.5 py-1 rounded-md text-[9px] font-black uppercase tracking-wider flex items-center gap-1 transition-all ${chatMode === "work"
                        ? "bg-[#1e3a8a] dark:bg-[#1e40af] text-white shadow-xs font-extrabold"
                        : "text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
                        }`}
                    >
                      <Sparkles className="h-3 w-3 text-[#93c5fd]" />
                      Work
                    </button>
                  </div>

                  {/* Model selector drop-up menu */}
                  <div className="relative">
                    <button
                      onClick={() => setShowModelDropdown(!showModelDropdown)}
                      className="flex items-center gap-1 text-[9px] font-bold uppercase tracking-widest text-slate-600 dark:text-slate-300 hover:text-[#1e3a8a] dark:hover:text-[#93c5fd] bg-white dark:bg-[#101828] border border-slate-200 dark:border-slate-700 px-2 py-1 rounded-lg shadow-xs transition-all"
                    >
                      <Cpu className="h-3 w-3 text-[#1e3a8a] dark:text-[#93c5fd] shrink-0" />
                      <span>{modelOptions.find((m) => m.name === chatModel)?.label}</span>
                      <ChevronRight className={`h-3 w-3 transition-transform ${showModelDropdown ? "-rotate-90" : "rotate-90"}`} />
                    </button>

                    {showModelDropdown && (
                      <div className="absolute right-0 bottom-full mb-1 w-48 bg-white dark:bg-[#101828] border border-slate-200 dark:border-slate-800 rounded-xl shadow-2xl p-1 z-50 animate-in fade-in slide-in-from-bottom-2 duration-150">
                        {modelOptions.map((opt) => (
                          <button
                            key={opt.name}
                            onClick={() => {
                              setChatModel(opt.name);
                              setShowModelDropdown(false);
                              setMessages((prev) => [
                                ...prev,
                                // Fake model transition message
                                { role: "assistant", content: `🤖 Switched active LLM engine parameter to: **${opt.name}**` }
                              ]);
                            }}
                            className={`w-full text-left px-2.5 py-1.5 rounded-lg text-[9px] font-semibold transition-colors flex items-center justify-between ${chatModel === opt.name
                              ? "bg-slate-100 dark:bg-slate-800 text-[#1e3a8a] dark:text-[#93c5fd] font-bold"
                              : "text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/50"
                              }`}
                          >
                            <span>{opt.label}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

              </div>
            </div>
          )}

        </div>
      )}
    </>
  );
}

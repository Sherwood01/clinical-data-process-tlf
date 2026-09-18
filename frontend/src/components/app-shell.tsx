"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useSessionContext, getAccessToken } from "supertokens-auth-react/recipe/session";
import { Sidebar } from "@/components/sidebar";
import { TopNav } from "@/components/top-nav";
import { UpgradeModal } from "@/components/billing/upgrade-modal";
import { ChatWidget } from "@/components/ai/chat-widget";

export function AppShell({ children }: { children: React.ReactNode }) {
  const session = useSessionContext();
  const params = useParams();
  const routeStudyId = params?.studyId as string | undefined;
  
  const [fallbackStudyId, setFallbackStudyId] = useState<string | null>(null);
  const [fallbackTenantId, setFallbackTenantId] = useState<string | null>(null);

  const doesSessionExist = session.loading ? false : session.doesSessionExist;

  // Fetch study list or details to populate the AI Agent's connection context (studyId and tenantId)
  useEffect(() => {
    if (session.loading || !doesSessionExist) return;

    let active = true;
    async function fetchStudyContext() {
      try {
        const token = await getAccessToken();
        if (routeStudyId) {
          // If on a specific study page, fetch that study to get its tenant_id
          const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "/api/v1"}/studies/${routeStudyId}`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (res.ok) {
            const data = await res.json();
            if (active) {
              setFallbackTenantId(data.tenant_id);
            }
          }
        } else {
          // If on a general page, fetch list to grab the first study and its tenant_id as fallback
          const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "/api/v1"}/studies`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (res.ok) {
            const list = await res.json();
            if (active && list && list.length > 0) {
              setFallbackStudyId(list[0].id);
              setFallbackTenantId(list[0].tenant_id);
            }
          }
        }
      } catch (err) {
        console.error("Failed to fetch study context for AI Agent shell:", err);
      }
    }
    fetchStudyContext();
    return () => {
      active = false;
    };
  }, [routeStudyId, session.loading, doesSessionExist]);

  const resolvedStudyId = routeStudyId || fallbackStudyId || "";
  const userId = session.loading ? "" : session.userId;
  const tenantId = userId;

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col min-w-0">
        <TopNav />
        <main className="flex-1 overflow-y-auto bg-muted/30 p-6">
          {children}
        </main>
      </div>
      <UpgradeModal />

      {!session.loading && session.doesSessionExist && (
        <ChatWidget
          studyId={resolvedStudyId}
          tenantId={tenantId}
          userId={userId}
        />
      )}
    </div>
  );
}


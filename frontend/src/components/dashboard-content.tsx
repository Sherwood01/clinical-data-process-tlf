"use client";

import { useSessionContext } from "supertokens-auth-react/recipe/session";
import { getAccessToken } from "supertokens-web-js/recipe/session";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useUserEmail } from "@/lib/use-user-email";

export default function DashboardContent() {
  const session = useSessionContext();
  const router = useRouter();
  const [studies, setStudies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newStudy, setNewStudy] = useState({ name: "", protocol_id: "", description: "" });
  const [creating, setCreating] = useState(false);
  const { email } = useUserEmail();

  useEffect(() => {
    if (session.loading) return;
    if (!session.doesSessionExist) {
      router.push("/auth/sign-in");
      return;
    }
    fetchStudies();
  }, [session.loading, session]);

  async function fetchStudies() {
    try {
      const token = await getAccessToken();
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/studies`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        setStudies(await res.json());
      }
    } catch (err) {
      console.error("Failed to fetch studies:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateStudy() {
    if (!newStudy.name.trim()) return;
    setCreating(true);
    try {
      const token = await getAccessToken();
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/studies`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(newStudy),
        }
      );
      if (res.ok) {
        const study = await res.json();
        setShowCreate(false);
        setNewStudy({ name: "", protocol_id: "", description: "" });
        router.push(`/studies/${study.id}`);
      }
    } catch (err) {
      console.error("Failed to create study:", err);
    } finally {
      setCreating(false);
    }
  }

  if (session.loading) return null;
  if (!session.doesSessionExist) return null;

  const displayName = email || (!session.loading ? session.userId : "") || "User";

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="font-bold text-lg">TLF Report Generator</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">{displayName}</span>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-bold">Studies</h1>
          <button
            onClick={() => setShowCreate(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm font-medium"
          >
            + New Study
          </button>
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-500">Loading...</div>
        ) : studies.length === 0 ? (
          <div className="text-center py-16">
            <div className="text-5xl mb-4">📋</div>
            <h2 className="text-xl font-semibold mb-2">No studies yet</h2>
            <p className="text-gray-500 mb-6">
              Create your first study to start generating TLF reports
            </p>
            <button
              onClick={() => setShowCreate(true)}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
            >
              Create Your First Study
            </button>
          </div>
        ) : (
          <div className="grid gap-4">
            {studies.map((study: any) => (
              <div
                key={study.id}
                onClick={() => router.push(`/studies/${study.id}`)}
                className="bg-white border rounded-lg p-6 hover:shadow-sm transition-shadow cursor-pointer"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-lg">{study.name}</h3>
                    {study.protocol_id && (
                      <p className="text-sm text-gray-500">{study.protocol_id}</p>
                    )}
                  </div>
                  <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                    {study.status}
                  </span>
                </div>
                {study.description && (
                  <p className="text-sm text-gray-500 mt-2 line-clamp-1">
                    {study.description}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Create Study Modal */}
        {showCreate && (
          <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-xl">
              <h2 className="text-lg font-semibold mb-4">Create New Study</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Study Name *</label>
                  <input
                    type="text"
                    value={newStudy.name}
                    onChange={(e) => setNewStudy({ ...newStudy, name: e.target.value })}
                    placeholder="e.g. Phase 3 RCT"
                    className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Protocol ID</label>
                  <input
                    type="text"
                    value={newStudy.protocol_id}
                    onChange={(e) => setNewStudy({ ...newStudy, protocol_id: e.target.value })}
                    placeholder="e.g. ABC-123"
                    className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea
                    value={newStudy.description}
                    onChange={(e) => setNewStudy({ ...newStudy, description: e.target.value })}
                    placeholder="Optional description"
                    rows={3}
                    className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => setShowCreate(false)}
                  className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateStudy}
                  disabled={!newStudy.name.trim() || creating}
                  className={`px-4 py-2 rounded-lg text-sm font-medium ${
                    !newStudy.name.trim() || creating
                      ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                      : "bg-blue-600 text-white hover:bg-blue-700"
                  }`}
                >
                  {creating ? "Creating..." : "Create Study"}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

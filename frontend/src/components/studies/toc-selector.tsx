"use client";

import { useState } from "react";

interface TOCEntry {
  id: string;
  tlf_id: string;
  tlf_type: string;
  tlf_name: string;
  population: string;
  analysis_type: string;
  is_generated: boolean;
}

interface TOCSelectorProps {
  entries: TOCEntry[];
  selectedIds: Set<string>;
  onSelectionChange: (ids: Set<string>) => void;
}

export function TOCSelector({
  entries,
  selectedIds,
  onSelectionChange,
}: TOCSelectorProps) {
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");

  const filteredEntries = entries.filter((e) => {
    if (typeFilter !== "all" && e.tlf_type !== typeFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        e.tlf_id.toLowerCase().includes(q) ||
        e.tlf_name.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const toggleEntry = (id: string) => {
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    onSelectionChange(next);
  };

  const selectAll = () => {
    onSelectionChange(new Set(filteredEntries.filter(e => !e.is_generated).map((e) => e.id)));
  };

  const deselectAll = () => {
    onSelectionChange(new Set());
  };

  const canGenerate = filteredEntries.filter((e) => !e.is_generated).length > 0;

  return (
    <div>
      {/* Filters */}
      <div className="flex items-center gap-3 mb-4">
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
          {["all", "table", "figure", "listing"].map((type) => (
            <button
              key={type}
              onClick={() => setTypeFilter(type)}
              className={`px-3 py-1.5 text-xs rounded-md font-medium transition-colors ${
                typeFilter === type
                  ? "bg-white text-gray-800 shadow-sm"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          ))}
        </div>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search TLF ID or name..."
          className="flex-1 max-w-xs px-3 py-1.5 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <span className="text-xs text-gray-500">
          {selectedIds.size} selected
        </span>
      </div>

      {/* Select / Deselect all */}
      <div className="flex items-center gap-3 mb-3">
        {canGenerate && (
          <>
            <button
              onClick={selectAll}
              className="text-xs text-blue-600 hover:underline"
            >
              Select All
            </button>
            <button
              onClick={deselectAll}
              className="text-xs text-gray-500 hover:underline"
            >
              Deselect All
            </button>
          </>
        )}
      </div>

      {/* Table */}
      <div className="bg-white border rounded-lg overflow-hidden max-h-96 overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b sticky top-0">
            <tr>
              <th className="w-10 px-4 py-3"></th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">
                TLF ID
              </th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">
                Type
              </th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">
                Name
              </th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">
                Population
              </th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {filteredEntries.map((entry) => (
              <tr
                key={entry.id}
                className={`hover:bg-gray-50 ${
                  entry.is_generated ? "opacity-50" : ""
                }`}
              >
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={selectedIds.has(entry.id)}
                    onChange={() => toggleEntry(entry.id)}
                    disabled={entry.is_generated}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </td>
                <td className="px-4 py-3 font-mono text-xs">{entry.tlf_id}</td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                      entry.tlf_type === "table"
                        ? "bg-blue-100 text-blue-700"
                        : entry.tlf_type === "figure"
                        ? "bg-purple-100 text-purple-700"
                        : "bg-orange-100 text-orange-700"
                    }`}
                  >
                    {entry.tlf_type}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-700 max-w-xs truncate">
                  {entry.tlf_name || "-"}
                </td>
                <td className="px-4 py-3 text-gray-500">
                  {entry.population || "-"}
                </td>
                <td className="px-4 py-3">
                  {entry.is_generated ? (
                    <span className="text-green-600 text-xs font-medium">
                      Generated
                    </span>
                  ) : (
                    <span className="text-gray-400 text-xs">Pending</span>
                  )}
                </td>
              </tr>
            ))}
            {filteredEntries.length === 0 && (
              <tr>
                <td
                  colSpan={6}
                  className="px-4 py-8 text-center text-gray-500"
                >
                  No matching TOC entries found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

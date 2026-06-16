"use client";

import { useState } from "react";
import { Badge, Input } from "@hexclave/ui";
import { Search, Table, Image, List, CheckSquare, Square } from "lucide-react";

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

const typeColors: Record<string, { variant: "default" | "secondary" | "outline"; icon: typeof Table }> = {
  table: { variant: "default", icon: Table },
  figure: { variant: "secondary", icon: Image },
  listing: { variant: "outline", icon: List },
};

function TypeBadge({ type }: { type: string }) {
  const config = typeColors[type] || { variant: "secondary" as const, icon: Table };
  const Icon = config.icon;
  return (
    <Badge variant={config.variant} className="gap-1 capitalize">
      <Icon className="h-3 w-3" />
      {type}
    </Badge>
  );
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
    onSelectionChange(new Set(filteredEntries.map((e) => e.id)));
  };

  const deselectAll = () => {
    onSelectionChange(new Set());
  };

  const filterTypes = ["all", "table", "figure", "listing"];

  return (
    <div>
      {/* Filters */}
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <div className="flex gap-1 bg-muted rounded-lg p-1">
          {filterTypes.map((type) => (
            <button
              key={type}
              onClick={() => setTypeFilter(type)}
              className={`px-3 py-1.5 text-xs rounded-md font-medium transition-colors ${
                typeFilter === type
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          ))}
        </div>
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search TLF ID or name..."
            className="pl-8 h-9 text-sm"
          />
        </div>
        <span className="text-xs text-muted-foreground whitespace-nowrap">
          {selectedIds.size} selected
        </span>
      </div>

      {/* Select / Deselect all */}
      <div className="flex items-center gap-3 mb-3">
        <button
          onClick={selectAll}
          className="text-xs text-primary hover:underline flex items-center gap-1"
        >
          <CheckSquare className="h-3 w-3" />
          Select All
        </button>
        <button
          onClick={deselectAll}
          className="text-xs text-muted-foreground hover:underline flex items-center gap-1"
        >
          <Square className="h-3 w-3" />
          Deselect All
        </button>
      </div>

      {/* Table */}
      <div className="rounded-xl border bg-card overflow-hidden max-h-96 overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 border-b sticky top-0">
            <tr>
              <th className="w-10 px-4 py-3"></th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">TLF ID</th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Type</th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Name</th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Population</th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {filteredEntries.map((entry) => (
              <tr
                key={entry.id}
                className="hover:bg-muted/30 transition-colors cursor-pointer"
                onClick={() => toggleEntry(entry.id)}
              >
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={selectedIds.has(entry.id)}
                    onChange={() => toggleEntry(entry.id)}
                    className="rounded border-input text-primary focus:ring-primary h-4 w-4"
                  />
                </td>
                <td className="px-4 py-3 font-mono text-xs">{entry.tlf_id}</td>
                <td className="px-4 py-3">
                  <TypeBadge type={entry.tlf_type} />
                </td>
                <td className="px-4 py-3 max-w-xs truncate">{entry.tlf_name || "-"}</td>
                <td className="px-4 py-3 text-muted-foreground">{entry.population || "-"}</td>
                <td className="px-4 py-3">
                  {entry.is_generated ? (
                    <span className="text-emerald-600 text-xs font-medium">Generated</span>
                  ) : (
                    <span className="text-muted-foreground text-xs">Pending</span>
                  )}
                </td>
              </tr>
            ))}
            {filteredEntries.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
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

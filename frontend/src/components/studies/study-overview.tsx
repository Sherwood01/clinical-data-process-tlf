"use client";

import { Badge } from "@hexclave/ui";
import { Database, FileText, FileOutput, CheckCircle2, FlaskConical } from "lucide-react";

interface StudyOverviewProps {
  study: any;
  datasets: any[];
  tocEntries: any[];
  tlfJobs: any[];
}

export function StudyOverview({
  study,
  datasets,
  tocEntries,
  tlfJobs,
}: StudyOverviewProps) {
  const generatedCount = tocEntries.filter((e: any) => e.is_generated).length;
  const completedJobs = tlfJobs.filter((j: any) => j.status === "completed").length;
  const failedJobs = tlfJobs.filter((j: any) => j.status === "failed").length;

  const statCards = [
    { label: "Datasets", value: datasets.length, icon: Database, color: "text-blue-600" },
    { label: "TOC Entries", value: tocEntries.length, icon: FileText, color: "text-purple-600" },
    { label: "Generated", value: generatedCount, icon: FileOutput, color: "text-emerald-600" },
    {
      label: "Jobs Completed",
      value: completedJobs,
      icon: CheckCircle2,
      color: "text-amber-600",
      extra: failedJobs > 0 ? `${failedJobs} failed` : undefined,
    },
  ];

  return (
    <div className="space-y-8">
      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.label}
              className="rounded-xl border bg-card p-5 flex items-center gap-4"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                <Icon className={`h-5 w-5 ${stat.color}`} />
              </div>
              <div>
                <p className="text-2xl font-bold">{stat.value}</p>
                <p className="text-sm text-muted-foreground">{stat.label}</p>
                {stat.extra && (
                  <p className="text-xs text-destructive mt-0.5">{stat.extra}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Study details */}
      <div className="rounded-xl border bg-card p-6">
        <div className="flex items-center gap-2 mb-5">
          <FlaskConical className="h-5 w-5 text-primary" />
          <h3 className="font-semibold">Study Details</h3>
        </div>
        <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-4 text-sm">
          <div>
            <dt className="text-muted-foreground text-xs uppercase tracking-wider mb-1">Name</dt>
            <dd className="font-medium">{study?.name || "-"}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground text-xs uppercase tracking-wider mb-1">Protocol ID</dt>
            <dd className="font-medium">{study?.protocol_id || "-"}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground text-xs uppercase tracking-wider mb-1">Status</dt>
            <dd>
              <Badge variant={study?.status === "completed" ? "default" : "secondary"}>
                {study?.status || "active"}
              </Badge>
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground text-xs uppercase tracking-wider mb-1">Created</dt>
            <dd className="font-medium">
              {study?.created_at
                ? new Date(study.created_at).toLocaleDateString()
                : "-"}
            </dd>
          </div>
        </dl>
        {study?.description && (
          <div className="mt-5 pt-5 border-t">
            <dt className="text-muted-foreground text-xs uppercase tracking-wider mb-1">Description</dt>
            <dd className="text-sm mt-1">{study.description}</dd>
          </div>
        )}
      </div>
    </div>
  );
}

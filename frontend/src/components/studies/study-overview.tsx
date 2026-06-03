"use client";

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

  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">Study Overview</h2>

      {/* Stat cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white border rounded-lg p-5">
          <div className="text-2xl font-bold text-gray-800">{datasets.length}</div>
          <div className="text-sm text-gray-500 mt-1">Datasets</div>
        </div>
        <div className="bg-white border rounded-lg p-5">
          <div className="text-2xl font-bold text-gray-800">{tocEntries.length}</div>
          <div className="text-sm text-gray-500 mt-1">TOC Entries</div>
        </div>
        <div className="bg-white border rounded-lg p-5">
          <div className="text-2xl font-bold text-green-600">{generatedCount}</div>
          <div className="text-sm text-gray-500 mt-1">Generated</div>
        </div>
        <div className="bg-white border rounded-lg p-5">
          <div className="text-2xl font-bold text-blue-600">{completedJobs}</div>
          <div className="text-sm text-gray-500 mt-1">Jobs Completed</div>
          {failedJobs > 0 && (
            <div className="text-xs text-red-500 mt-1">{failedJobs} failed</div>
          )}
        </div>
      </div>

      {/* Study info */}
      <div className="bg-white border rounded-lg p-6">
        <h3 className="font-semibold mb-3">Study Details</h3>
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="text-gray-500">Name</dt>
            <dd className="font-medium">{study?.name || "-"}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Protocol ID</dt>
            <dd className="font-medium">{study?.protocol_id || "-"}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Status</dt>
            <dd>
              <span className="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                {study?.status || "active"}
              </span>
            </dd>
          </div>
          <div>
            <dt className="text-gray-500">Created</dt>
            <dd className="font-medium">
              {study?.created_at
                ? new Date(study.created_at).toLocaleDateString()
                : "-"}
            </dd>
          </div>
        </dl>
        {study?.description && (
          <div className="mt-4">
            <dt className="text-sm text-gray-500">Description</dt>
            <dd className="text-sm mt-1">{study.description}</dd>
          </div>
        )}
      </div>
    </div>
  );
}

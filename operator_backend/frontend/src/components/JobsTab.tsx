import React, { useEffect, useState } from "react";
import { listJobs, getJobDetail } from "../api/canonical";
import { OperatorJob, ErrorResponse } from "../types/canonical";

export const JobsTab: React.FC = () => {
    const [jobs, setJobs] = useState<OperatorJob[]>([]);
    const [selectedJob, setSelectedJob] = useState<OperatorJob | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [skip, setSkip] = useState(0);
    const [total, setTotal] = useState(0);

    const PAGE_SIZE = 10;

    useEffect(() => {
        fetchJobs();
    }, [skip]);

    const fetchJobs = async () => {
        setLoading(true);
        const result = await listJobs(skip, PAGE_SIZE);

        if ("error" in result) {
            const err = result as ErrorResponse;
            setError(err.error || "Failed to load jobs");
            setJobs([]);
        } else {
            setJobs(result.jobs || []);
            setTotal(result.total || 0);
            setError(null);
        }

        setLoading(false);
    };

    const handleJobClick = async (job: OperatorJob) => {
        const result = await getJobDetail(job.id);

        if ("error" in result) {
            setError(`Failed to load job detail: ${(result as ErrorResponse).error}`);
        } else {
            setSelectedJob(result);
        }
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Jobs List */}
            <div className="lg:col-span-1">
                <h3 className="text-lg font-semibold text-white mb-4">Jobs</h3>

                {error && (
                    <div className="p-4 bg-red-900 border-l-4 border-red-500 rounded mb-4">
                        <p className="text-red-100 text-sm">{error}</p>
                    </div>
                )}

                {loading ? (
                    <div className="text-slate-400">Loading...</div>
                ) : (
                    <>
                        <div className="space-y-2 mb-4">
                            {jobs.length === 0 ? (
                                <p className="text-slate-400">No jobs available</p>
                            ) : (
                                jobs.map((job) => (
                                    <button
                                        key={job.id}
                                        onClick={() => handleJobClick(job)}
                                        className={`w-full text-left p-3 rounded border transition-colors ${selectedJob?.id === job.id
                                            ? "bg-blue-600 border-blue-500 text-white"
                                            : "bg-slate-700 border-slate-600 text-slate-100 hover:bg-slate-600"
                                            }`}
                                    >
                                        <p className="font-medium text-sm truncate">{job.intent}</p>
                                        <p className="text-xs text-slate-400 mt-1">
                                            <span
                                                className={`inline-block w-2 h-2 rounded-full mr-1 ${job.status === "completed"
                                                    ? "bg-green-500"
                                                    : job.status === "failed"
                                                        ? "bg-red-500"
                                                        : "bg-blue-500"
                                                    }`}
                                            />
                                            {job.status}
                                        </p>
                                    </button>
                                ))
                            )}
                        </div>

                        {/* Pagination */}
                        {total > PAGE_SIZE && (
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setSkip(Math.max(0, skip - PAGE_SIZE))}
                                    disabled={skip === 0}
                                    className="flex-1 px-3 py-2 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 text-white rounded text-sm font-medium"
                                >
                                    ← Prev
                                </button>
                                <button
                                    onClick={() => setSkip(skip + PAGE_SIZE)}
                                    disabled={skip + PAGE_SIZE >= total}
                                    className="flex-1 px-3 py-2 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 text-white rounded text-sm font-medium"
                                >
                                    Next →
                                </button>
                            </div>
                        )}
                    </>
                )}
            </div>

            {/* Job Detail */}
            <div className="lg:col-span-2">
                {selectedJob ? (
                    <div className="bg-slate-700 rounded-lg p-6 border border-slate-600">
                        <h4 className="text-lg font-semibold text-white mb-4">Job Detail</h4>

                        <div className="space-y-3">
                            <div>
                                <p className="text-slate-300 text-xs font-medium mb-1">ID</p>
                                <p className="text-white font-mono text-sm">{selectedJob.id}</p>
                            </div>

                            <div>
                                <p className="text-slate-300 text-xs font-medium mb-1">Intent</p>
                                <p className="text-white">{selectedJob.intent}</p>
                            </div>

                            <div>
                                <p className="text-slate-300 text-xs font-medium mb-1">Status</p>
                                <div className="flex items-center gap-2">
                                    <span
                                        className={`inline-block w-3 h-3 rounded-full ${selectedJob.status === "completed"
                                            ? "bg-green-500"
                                            : selectedJob.status === "failed"
                                                ? "bg-red-500"
                                                : "bg-blue-500"
                                            }`}
                                    />
                                    <span className="text-white capitalize">{selectedJob.status}</span>
                                </div>
                            </div>

                            {selectedJob.progress !== undefined && (
                                <div>
                                    <p className="text-slate-300 text-xs font-medium mb-2">Progress</p>
                                    <div className="w-full bg-slate-600 rounded-full h-2">
                                        <div
                                            className="bg-blue-500 h-2 rounded-full transition-all duration-300 progress-bar"
                                            data-progress={selectedJob.progress}
                                        />
                                    </div>
                                    <p className="text-slate-400 text-xs mt-1">{selectedJob.progress}%</p>
                                </div>
                            )}

                            <div>
                                <p className="text-slate-300 text-xs font-medium mb-1">Created</p>
                                <p className="text-slate-400 text-sm">{new Date(selectedJob.created_at).toLocaleString()}</p>
                            </div>

                            <div>
                                <p className="text-slate-300 text-xs font-medium mb-1">Updated</p>
                                <p className="text-slate-400 text-sm">{new Date(selectedJob.updated_at).toLocaleString()}</p>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="bg-slate-700 rounded-lg p-6 border border-slate-600 text-slate-400 text-center py-12">
                        Select a job to view details
                    </div>
                )}
            </div>
        </div>
    );
};

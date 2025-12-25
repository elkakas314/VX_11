import { useState } from 'react'

interface AuditLog {
    timestamp: string
    action: string
    service?: string
    status: 'success' | 'error' | 'info'
    details?: string
}

export function AuditViewer() {
    const [logs] = useState<AuditLog[]>([
        {
            timestamp: new Date(Date.now() - 5000).toISOString(),
            action: 'Policy Applied',
            service: 'madre',
            status: 'success',
            details: 'solo_madre policy activated'
        },
        {
            timestamp: new Date(Date.now() - 10000).toISOString(),
            action: 'Service Started',
            service: 'switch',
            status: 'success',
            details: 'Switch container started successfully'
        },
    ])

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'success': return 'bg-green-900/50 text-green-300 border-green-700'
            case 'error': return 'bg-red-900/50 text-red-300 border-red-700'
            default: return 'bg-blue-900/50 text-blue-300 border-blue-700'
        }
    }

    return (
        <div className="space-y-6">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-100">Audit Log</h1>
                <p className="text-gray-400 mt-2">System events and actions history</p>
            </div>

            {/* Filter & Search */}
            <div className="flex gap-2 mb-4">
                <input
                    type="text"
                    placeholder="Search logs..."
                    className="flex-1 bg-slate-900 border border-gray-700 rounded-lg px-3 py-2 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-purple-500"
                />
                <button className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-medium transition">
                    Filter
                </button>
            </div>

            {/* Logs Table */}
            <div className="bg-slate-900 border border-gray-700 rounded-lg overflow-hidden">
                <table className="w-full">
                    <thead className="bg-slate-800 border-b border-gray-700">
                        <tr>
                            <th className="text-left px-4 py-3 text-sm font-semibold text-gray-300">Timestamp</th>
                            <th className="text-left px-4 py-3 text-sm font-semibold text-gray-300">Action</th>
                            <th className="text-left px-4 py-3 text-sm font-semibold text-gray-300">Service</th>
                            <th className="text-left px-4 py-3 text-sm font-semibold text-gray-300">Status</th>
                            <th className="text-left px-4 py-3 text-sm font-semibold text-gray-300">Details</th>
                        </tr>
                    </thead>
                    <tbody>
                        {logs.map((log, idx) => (
                            <tr key={idx} className="border-b border-gray-800 hover:bg-slate-800/50 transition">
                                <td className="px-4 py-3 text-sm text-gray-400">
                                    {new Date(log.timestamp).toLocaleString()}
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-100 font-medium">{log.action}</td>
                                <td className="px-4 py-3 text-sm text-gray-300 capitalize">{log.service || '-'}</td>
                                <td className="px-4 py-3 text-sm">
                                    <span className={`px-2 py-1 rounded text-xs font-medium border ${getStatusColor(log.status)}`}>
                                        {log.status.toUpperCase()}
                                    </span>
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-400">{log.details || '-'}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4">
                <div className="bg-slate-900 border border-green-900/50 rounded-lg p-4">
                    <h3 className="text-sm text-gray-400 uppercase tracking-wide">Success</h3>
                    <p className="text-2xl font-bold text-green-400 mt-2">
                        {logs.filter(l => l.status === 'success').length}
                    </p>
                </div>

                <div className="bg-slate-900 border border-red-900/50 rounded-lg p-4">
                    <h3 className="text-sm text-gray-400 uppercase tracking-wide">Errors</h3>
                    <p className="text-2xl font-bold text-red-400 mt-2">
                        {logs.filter(l => l.status === 'error').length}
                    </p>
                </div>

                <div className="bg-slate-900 border border-blue-900/50 rounded-lg p-4">
                    <h3 className="text-sm text-gray-400 uppercase tracking-wide">Total Events</h3>
                    <p className="text-2xl font-bold text-blue-400 mt-2">{logs.length}</p>
                </div>
            </div>
        </div>
    )
}

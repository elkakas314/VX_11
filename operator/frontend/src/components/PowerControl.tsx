import { useState } from 'react'
import { apiClient } from '../api/client'

const SERVICES = ['switch', 'hermes', 'hormiguero', 'tentaculo_link', 'spawner', 'mcp']

export function PowerControl() {
    const [loading, setLoading] = useState<string | null>(null)
    const [success, setSuccess] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)

    const handleSoloMadre = async () => {
        setLoading('solo_madre')
        setError(null)
        try {
            await apiClient.applySoloMadre()
            setSuccess('Solo Madre policy applied!')
            setTimeout(() => setSuccess(null), 3000)
        } catch (err: any) {
            setError(err.message || 'Failed to apply solo madre')
        } finally {
            setLoading(null)
        }
    }

    const handleStartService = async (service: string) => {
        setLoading(`start_${service}`)
        setError(null)
        try {
            await apiClient.startService(service)
            setSuccess(`${service} started!`)
            setTimeout(() => setSuccess(null), 3000)
        } catch (err: any) {
            setError(err.message || `Failed to start ${service}`)
        } finally {
            setLoading(null)
        }
    }

    const handleStopService = async (service: string) => {
        setLoading(`stop_${service}`)
        setError(null)
        try {
            await apiClient.stopService(service)
            setSuccess(`${service} stopped!`)
            setTimeout(() => setSuccess(null), 3000)
        } catch (err: any) {
            setError(err.message || `Failed to stop ${service}`)
        } finally {
            setLoading(null)
        }
    }

    return (
        <div className="space-y-6">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-100">Power Manager</h1>
                <p className="text-gray-400 mt-2">Container-level service control</p>
            </div>

            {/* Alerts */}
            {success && (
                <div className="bg-green-900/50 border border-green-500 rounded-lg p-4 text-green-300">
                    ✓ {success}
                </div>
            )}
            {error && (
                <div className="bg-red-900/50 border border-red-500 rounded-lg p-4 text-red-300">
                    ✗ {error}
                </div>
            )}

            {/* Solo Madre Policy */}
            <div className="bg-slate-900 border border-purple-900/50 rounded-lg p-6">
                <h2 className="text-xl font-semibold text-gray-100 mb-4">SOLO MADRE Policy</h2>
                <p className="text-gray-400 text-sm mb-4">
                    Stop all services except Madre (orchestrator) and Redis (cache).
                </p>
                <button
                    onClick={handleSoloMadre}
                    disabled={loading === 'solo_madre'}
                    className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white px-6 py-2 rounded-lg font-medium transition"
                >
                    {loading === 'solo_madre' ? 'Applying...' : 'Apply SOLO MADRE'}
                </button>
            </div>

            {/* Service Controls */}
            <div className="space-y-4">
                <h2 className="text-xl font-semibold text-gray-100">Service Controls</h2>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {SERVICES.map(service => (
                        <div key={service} className="bg-slate-900 border border-gray-700 rounded-lg p-4">
                            <div className="flex items-center justify-between mb-3">
                                <span className="font-medium text-gray-100 capitalize">{service}</span>
                                <span className="text-xs bg-gray-800 px-2 py-1 rounded text-gray-400">8{Math.random().toString().slice(2, 5).slice(0, 3)}</span>
                            </div>

                            <div className="flex gap-2">
                                <button
                                    onClick={() => handleStartService(service)}
                                    disabled={loading?.startsWith('start_')}
                                    className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white px-3 py-2 rounded text-sm font-medium transition"
                                >
                                    {loading === `start_${service}` ? 'Starting...' : 'Start'}
                                </button>

                                <button
                                    onClick={() => handleStopService(service)}
                                    disabled={loading?.startsWith('stop_')}
                                    className="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 text-white px-3 py-2 rounded text-sm font-medium transition"
                                >
                                    {loading === `stop_${service}` ? 'Stopping...' : 'Stop'}
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Info Box */}
            <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4">
                <h3 className="font-semibold text-blue-300 mb-2">⚠️ Important</h3>
                <p className="text-blue-200 text-sm">
                    All service control is container-level only. Individual process management is not supported.
                </p>
            </div>
        </div>
    )
}

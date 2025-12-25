import { useEffect, useState } from 'react'
import { apiClient } from '../api/client'

const MODULE_COLORS: Record<string, string> = {
    madre: 'bg-purple-900/50 border-purple-500',
    switch: 'bg-blue-900/50 border-blue-500',
    hermes: 'bg-amber-900/50 border-amber-500',
    spawner: 'bg-cyan-900/50 border-cyan-500',
    hormiguero: 'bg-green-900/50 border-green-500',
    tentaculo_link: 'bg-red-900/50 border-red-500',
    shubniggurath: 'bg-indigo-900/50 border-indigo-500',
    mcp: 'bg-pink-900/50 border-pink-500',
}

interface ServiceCard {
    name: string
    status: 'up' | 'down' | 'loading'
    latency?: number
}

export function Dashboard() {
    const [services, setServices] = useState<ServiceCard[]>([
        { name: 'madre', status: 'loading' },
        { name: 'switch', status: 'loading' },
        { name: 'hermes', status: 'loading' },
        { name: 'hormiguero', status: 'loading' },
    ])
    const [powerPolicy, setPowerPolicy] = useState<string>('solo_madre')
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const health = await apiClient.getMadreHealth()
                const power = await apiClient.getPowerStatus()

                setServices(prev => prev.map(s => ({
                    ...s,
                    status: health.status === 'ok' ? 'up' : 'down'
                })))

                setPowerPolicy(power.policy_active || 'solo_madre')
            } catch (err) {
                console.error('Failed to fetch status:', err)
            } finally {
                setLoading(false)
            }
        }

        fetchStatus()
        const interval = setInterval(fetchStatus, 5000)
        return () => clearInterval(interval)
    }, [])

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-100">VX11 Dashboard</h1>
                <p className="text-gray-400 mt-2">System Status & Module Health</p>
            </div>

            {/* Power Policy Card */}
            <div className="bg-slate-900 border border-purple-900/50 rounded-lg p-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-lg font-semibold text-gray-100">Power Policy</h2>
                        <p className="text-gray-400 text-sm mt-1">Current operational mode</p>
                    </div>
                    <div className="text-2xl font-bold text-purple-400 uppercase">{powerPolicy}</div>
                </div>
            </div>

            {/* Services Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {services.map(service => (
                    <div
                        key={service.name}
                        className={`border rounded-lg p-4 transition-all ${MODULE_COLORS[service.name] || 'bg-gray-900 border-gray-700'}`}
                    >
                        <div className="flex items-start justify-between">
                            <div>
                                <h3 className="font-semibold text-gray-100 capitalize">{service.name}</h3>
                                <div className="mt-2 flex items-center gap-2">
                                    <div className={`w-3 h-3 rounded-full ${service.status === 'up' ? 'bg-green-500 animate-pulse' :
                                        service.status === 'loading' ? 'bg-yellow-500 animate-pulse' :
                                            'bg-red-500'
                                        }`}></div>
                                    <span className="text-sm text-gray-300 capitalize">{service.status}</span>
                                </div>
                            </div>
                            {service.latency && (
                                <div className="text-right text-xs text-gray-400">
                                    {service.latency}ms
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {/* Core Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
                <div className="bg-slate-900 border border-gray-700 rounded-lg p-4">
                    <h3 className="text-sm text-gray-400 uppercase tracking-wide">Healthy Services</h3>
                    <p className="text-2xl font-bold text-green-400 mt-2">
                        {services.filter(s => s.status === 'up').length}/{services.length}
                    </p>
                </div>

                <div className="bg-slate-900 border border-gray-700 rounded-lg p-4">
                    <h3 className="text-sm text-gray-400 uppercase tracking-wide">Avg Latency</h3>
                    <p className="text-2xl font-bold text-blue-400 mt-2">
                        {services.reduce((sum, s) => sum + (s.latency || 0), 0) / services.length || 0}ms
                    </p>
                </div>

                <div className="bg-slate-900 border border-gray-700 rounded-lg p-4">
                    <h3 className="text-sm text-gray-400 uppercase tracking-wide">Last Updated</h3>
                    <p className="text-sm text-gray-300 mt-2">
                        {new Date().toLocaleTimeString()}
                    </p>
                </div>
            </div>

            {loading && (
                <div className="text-center py-12">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-2 border-purple-500 border-t-transparent"></div>
                    <p className="text-gray-400 mt-2">Loading system status...</p>
                </div>
            )}
        </div>
    )
}
